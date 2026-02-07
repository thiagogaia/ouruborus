#!/usr/bin/env python3
"""
diff_parser.py - Parse unified diffs and classify changes

Extracts structured information from git unified diffs:
- File-level changes (added, modified, deleted, renamed)
- Symbol-level changes (functions, classes added/modified/deleted)
- Change shape classification (tiny_fix, feature_add, refactor, etc.)
- Summary generation (~500 tokens max)

All classification is heuristic — no LLM, deterministic, fast, zero cost.

Usage (standalone test):
    python3 diff_parser.py <commit_hash>
    python3 diff_parser.py --stdin < diff.patch
"""

import re
import sys
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple


# ══════════════════════════════════════════════════════════
# DATA STRUCTURES
# ══════════════════════════════════════════════════════════

@dataclass
class Hunk:
    """A single hunk from a unified diff."""
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    header: str  # function/class context from @@ line
    added_lines: List[str] = field(default_factory=list)
    removed_lines: List[str] = field(default_factory=list)
    context_lines: List[str] = field(default_factory=list)


@dataclass
class FileDiff:
    """Parsed diff for a single file."""
    old_path: str
    new_path: str
    status: str  # "added", "modified", "deleted", "renamed"
    hunks: List[Hunk] = field(default_factory=list)
    is_binary: bool = False

    @property
    def insertions(self) -> int:
        return sum(len(h.added_lines) for h in self.hunks)

    @property
    def deletions(self) -> int:
        return sum(len(h.removed_lines) for h in self.hunks)

    @property
    def path(self) -> str:
        """Primary file path (new_path for renames, otherwise whichever exists)."""
        return self.new_path if self.new_path != "/dev/null" else self.old_path


@dataclass
class SymbolChange:
    """A detected symbol change."""
    kind: str  # "function", "class", "interface", "method"
    name: str
    change_type: str  # "added", "modified", "deleted"
    file_path: str


@dataclass
class DiffSummary:
    """Complete diff analysis for a commit."""
    files: List[FileDiff]
    symbols_added: List[SymbolChange]
    symbols_modified: List[SymbolChange]
    symbols_deleted: List[SymbolChange]
    change_shape: str
    diff_stats: dict  # {files_changed, insertions, deletions}
    summary_text: str  # ~500 tokens max


# ══════════════════════════════════════════════════════════
# FILTERS
# ══════════════════════════════════════════════════════════

# Skip these paths entirely
SKIP_PATTERNS = [
    r'node_modules/', r'vendor/', r'\.venv/', r'__pycache__/',
    r'\.git/', r'dist/', r'build/', r'\.next/', r'\.nuxt/',
    r'coverage/', r'\.tox/', r'\.mypy_cache/',
]

SKIP_EXTENSIONS = {
    '.lock', '.sum', '.min.js', '.min.css',
    '.map', '.snap', '.svg', '.png', '.jpg', '.jpeg', '.gif',
    '.ico', '.woff', '.woff2', '.ttf', '.eot',
    '.pyc', '.pyo', '.class', '.o', '.so', '.dylib',
    '.db', '.sqlite', '.sqlite3',
}

GENERATED_PATTERNS = [
    r'package-lock\.json$', r'yarn\.lock$', r'pnpm-lock\.yaml$',
    r'Gemfile\.lock$', r'Cargo\.lock$', r'poetry\.lock$',
    r'go\.sum$', r'composer\.lock$',
    r'\.generated\.', r'_generated\.',
]

MAX_DIFF_LINES = 5000


def should_skip_file(path: str) -> bool:
    """Check if a file should be skipped from diff analysis."""
    if not path or path == "/dev/null":
        return False

    for pattern in SKIP_PATTERNS:
        if re.search(pattern, path):
            return True

    ext = Path(path).suffix.lower()
    if ext in SKIP_EXTENSIONS:
        return True

    for pattern in GENERATED_PATTERNS:
        if re.search(pattern, path):
            return True

    return False


# ══════════════════════════════════════════════════════════
# PARSER (state machine)
# ══════════════════════════════════════════════════════════

def parse_unified_diff(diff_text: str) -> List[FileDiff]:
    """Parse unified diff text into structured FileDiff objects.

    State machine:
    - HEADER: looking for --- / +++
    - HUNK: inside a hunk, collecting +/- lines
    """
    files = []
    current_file: Optional[FileDiff] = None
    current_hunk: Optional[Hunk] = None
    line_count = 0

    for line in diff_text.split('\n'):
        line_count += 1
        if line_count > MAX_DIFF_LINES:
            break

        # New file diff header
        if line.startswith('diff --git'):
            # Save previous hunk/file
            if current_hunk and current_file:
                current_file.hunks.append(current_hunk)
                current_hunk = None
            if current_file:
                files.append(current_file)

            # Extract paths from diff --git a/path b/path
            m = re.match(r'diff --git a/(.+?) b/(.+)', line)
            if m:
                current_file = FileDiff(
                    old_path=m.group(1),
                    new_path=m.group(2),
                    status="modified"
                )
            else:
                current_file = FileDiff(old_path="", new_path="", status="modified")
            continue

        if current_file is None:
            continue

        # Binary file detection
        if line.startswith('Binary files'):
            current_file.is_binary = True
            continue

        # File status markers
        if line.startswith('new file mode'):
            current_file.status = "added"
            continue
        if line.startswith('deleted file mode'):
            current_file.status = "deleted"
            continue
        if line.startswith('rename from') or line.startswith('similarity index'):
            current_file.status = "renamed"
            continue

        # --- and +++ lines (confirm/update paths)
        if line.startswith('--- '):
            path = line[4:]
            if path.startswith('a/'):
                path = path[2:]
            if path == '/dev/null':
                current_file.status = "added"
            current_file.old_path = path
            continue
        if line.startswith('+++ '):
            path = line[4:]
            if path.startswith('b/'):
                path = path[2:]
            if path == '/dev/null':
                current_file.status = "deleted"
            current_file.new_path = path
            continue

        # Hunk header: @@ -old_start,old_count +new_start,new_count @@ context
        hunk_match = re.match(
            r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@\s*(.*)',
            line
        )
        if hunk_match:
            if current_hunk:
                current_file.hunks.append(current_hunk)
            current_hunk = Hunk(
                old_start=int(hunk_match.group(1)),
                old_count=int(hunk_match.group(2) or 1),
                new_start=int(hunk_match.group(3)),
                new_count=int(hunk_match.group(4) or 1),
                header=hunk_match.group(5).strip()
            )
            continue

        # Hunk content
        if current_hunk is not None:
            if line.startswith('+'):
                current_hunk.added_lines.append(line[1:])
            elif line.startswith('-'):
                current_hunk.removed_lines.append(line[1:])
            elif line.startswith(' '):
                current_hunk.context_lines.append(line[1:])

    # Save last hunk/file
    if current_hunk and current_file:
        current_file.hunks.append(current_hunk)
    if current_file:
        files.append(current_file)

    return files


# ══════════════════════════════════════════════════════════
# SYMBOL DETECTION
# ══════════════════════════════════════════════════════════

# Patterns to detect symbol definitions across languages
SYMBOL_PATTERNS = [
    # Python
    (r'^\s*def\s+(\w+)\s*\(', 'function'),
    (r'^\s*async\s+def\s+(\w+)\s*\(', 'function'),
    (r'^\s*class\s+(\w+)', 'class'),

    # JavaScript/TypeScript
    (r'^\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)', 'function'),
    (r'^\s*(?:export\s+)?(?:default\s+)?class\s+(\w+)', 'class'),
    (r'^\s*(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\(', 'function'),
    (r'^\s*(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?function', 'function'),
    (r'^\s*(?:export\s+)?interface\s+(\w+)', 'interface'),
    (r'^\s*(?:export\s+)?type\s+(\w+)\s*=', 'interface'),

    # Ruby
    (r'^\s*def\s+(\w+)', 'function'),
    (r'^\s*class\s+(\w+)', 'class'),
    (r'^\s*module\s+(\w+)', 'class'),

    # Go
    (r'^\s*func\s+(?:\(\w+\s+\*?\w+\)\s+)?(\w+)\s*\(', 'function'),
    (r'^\s*type\s+(\w+)\s+struct', 'class'),
    (r'^\s*type\s+(\w+)\s+interface', 'interface'),

    # Java / Rust / PHP
    (r'^\s*(?:public|private|protected|static|final|abstract|async)?\s*(?:public|private|protected|static|final|abstract|async)?\s*(?:\w+\s+)?(\w+)\s*\([^)]*\)\s*(?:throws\s+\w+\s*)?{', 'function'),
    (r'^\s*(?:pub\s+)?(?:async\s+)?fn\s+(\w+)', 'function'),
    (r'^\s*(?:pub\s+)?struct\s+(\w+)', 'class'),
    (r'^\s*(?:pub\s+)?trait\s+(\w+)', 'interface'),
    (r'^\s*(?:pub\s+)?enum\s+(\w+)', 'class'),
    (r'^\s*(?:pub\s+)?impl\s+(?:\w+\s+for\s+)?(\w+)', 'class'),
]


def _detect_symbols_in_lines(lines: List[str]) -> List[Tuple[str, str]]:
    """Detect symbol definitions in a list of lines.

    Returns: [(name, kind)] pairs.
    """
    symbols = []
    seen = set()

    for line in lines:
        stripped = line.rstrip()
        for pattern, kind in SYMBOL_PATTERNS:
            m = re.match(pattern, stripped)
            if m:
                name = m.group(1)
                key = f"{kind}:{name}"
                if key not in seen:
                    symbols.append((name, kind))
                    seen.add(key)
                break  # first match wins per line

    return symbols


def classify_symbols(file_diffs: List[FileDiff]) -> Tuple[
    List[SymbolChange], List[SymbolChange], List[SymbolChange]
]:
    """Classify symbol changes from file diffs.

    Logic:
    - Symbol in added lines only → added
    - Symbol in removed lines only → deleted
    - Symbol in both added AND removed lines in same hunk → modified
    """
    added = []
    modified = []
    deleted = []

    for fd in file_diffs:
        if fd.is_binary or should_skip_file(fd.path):
            continue

        for hunk in fd.hunks:
            added_syms = set(f"{k}:{n}" for n, k in _detect_symbols_in_lines(hunk.added_lines))
            removed_syms = set(f"{k}:{n}" for n, k in _detect_symbols_in_lines(hunk.removed_lines))

            # Modified: appears in both added and removed
            for sym_key in added_syms & removed_syms:
                kind, name = sym_key.split(':', 1)
                modified.append(SymbolChange(
                    kind=kind, name=name,
                    change_type="modified", file_path=fd.path
                ))

            # Added: only in added lines
            for sym_key in added_syms - removed_syms:
                kind, name = sym_key.split(':', 1)
                added.append(SymbolChange(
                    kind=kind, name=name,
                    change_type="added", file_path=fd.path
                ))

            # Deleted: only in removed lines
            for sym_key in removed_syms - added_syms:
                kind, name = sym_key.split(':', 1)
                deleted.append(SymbolChange(
                    kind=kind, name=name,
                    change_type="deleted", file_path=fd.path
                ))

        # Also check hunk headers for context (function being modified)
        for hunk in fd.hunks:
            if hunk.header:
                ctx_syms = _detect_symbols_in_lines([hunk.header])
                for name, kind in ctx_syms:
                    key = f"{kind}:{name}"
                    # Only add as modified if not already captured
                    already = any(
                        s.name == name and s.kind == kind and s.file_path == fd.path
                        for s in added + modified + deleted
                    )
                    if not already and (hunk.added_lines or hunk.removed_lines):
                        modified.append(SymbolChange(
                            kind=kind, name=name,
                            change_type="modified", file_path=fd.path
                        ))

    return added, modified, deleted


# ══════════════════════════════════════════════════════════
# CHANGE SHAPE CLASSIFICATION
# ══════════════════════════════════════════════════════════

def classify_change_shape(
    file_diffs: List[FileDiff],
    symbols_added: List[SymbolChange],
    symbols_modified: List[SymbolChange],
    symbols_deleted: List[SymbolChange]
) -> str:
    """Classify the overall shape of a commit's changes.

    Categories:
    - tiny_fix: <10 lines changed, no new symbols
    - small_fix: <30 lines changed, no new symbols
    - feature_add: new symbols added
    - feature_modify: mostly modifications to existing symbols
    - refactor: roughly equal adds/deletes, same symbols
    - large_refactor: >200 lines, balanced add/delete
    - config_change: only config/infra files
    - documentation: only docs/markdown/comments
    - test: only test files
    """
    total_insertions = sum(fd.insertions for fd in file_diffs if not fd.is_binary)
    total_deletions = sum(fd.deletions for fd in file_diffs if not fd.is_binary)
    total_changes = total_insertions + total_deletions
    file_paths = [fd.path for fd in file_diffs if not fd.is_binary]

    # Check file categories
    config_exts = {'.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.env', '.conf'}
    doc_exts = {'.md', '.rst', '.txt', '.adoc'}
    test_patterns = [r'test[_/]', r'spec[_/]', r'_test\.', r'\.test\.', r'\.spec\.']

    all_config = all(Path(p).suffix.lower() in config_exts for p in file_paths) if file_paths else False
    all_docs = all(Path(p).suffix.lower() in doc_exts for p in file_paths) if file_paths else False
    all_tests = all(any(re.search(pat, p) for pat in test_patterns) for p in file_paths) if file_paths else False

    if all_docs and file_paths:
        return "documentation"
    if all_tests and file_paths:
        return "test"
    if all_config and file_paths:
        return "config_change"

    # Size-based classification
    has_new_symbols = len(symbols_added) > 0
    has_deleted_symbols = len(symbols_deleted) > 0

    if total_changes < 10 and not has_new_symbols:
        return "tiny_fix"
    if total_changes < 30 and not has_new_symbols:
        return "small_fix"

    # Refactor detection: balanced add/delete ratio
    if total_insertions > 0 and total_deletions > 0:
        ratio = min(total_insertions, total_deletions) / max(total_insertions, total_deletions)
        if ratio > 0.6 and total_changes > 50:
            if total_changes > 200:
                return "large_refactor"
            return "refactor"

    if has_new_symbols:
        return "feature_add"
    if symbols_modified:
        return "feature_modify"

    if total_changes < 30:
        return "small_fix"

    return "feature_modify"


# ══════════════════════════════════════════════════════════
# SUMMARY GENERATION
# ══════════════════════════════════════════════════════════

def generate_summary(
    file_diffs: List[FileDiff],
    symbols_added: List[SymbolChange],
    symbols_modified: List[SymbolChange],
    symbols_deleted: List[SymbolChange],
    change_shape: str,
    max_tokens: int = 500
) -> str:
    """Generate a textual summary of the diff (~500 tokens max).

    Format:
    Shape: <shape> (N files, +X -Y)
    Added: <symbol_list>
    Modified: <symbol_list>
    Deleted: <symbol_list>
    Files: <file_list>
    """
    parts = []

    # Stats line
    files_changed = len([fd for fd in file_diffs if not fd.is_binary])
    total_ins = sum(fd.insertions for fd in file_diffs if not fd.is_binary)
    total_del = sum(fd.deletions for fd in file_diffs if not fd.is_binary)
    parts.append(f"Shape: {change_shape} ({files_changed} files, +{total_ins} -{total_del})")

    # Symbols
    if symbols_added:
        sym_strs = [f"{s.kind}:{s.name}" for s in symbols_added[:10]]
        parts.append(f"Added: {', '.join(sym_strs)}")

    if symbols_modified:
        sym_strs = [f"{s.kind}:{s.name}" for s in symbols_modified[:10]]
        parts.append(f"Modified: {', '.join(sym_strs)}")

    if symbols_deleted:
        sym_strs = [f"{s.kind}:{s.name}" for s in symbols_deleted[:10]]
        parts.append(f"Deleted: {', '.join(sym_strs)}")

    # Files (top 10)
    file_paths = [fd.path for fd in file_diffs if not fd.is_binary][:10]
    if file_paths:
        parts.append(f"Files: {', '.join(file_paths)}")

    result = '\n'.join(parts)

    # Rough token limit (4 chars ~ 1 token)
    max_chars = max_tokens * 4
    if len(result) > max_chars:
        result = result[:max_chars - 3] + "..."

    return result


# ══════════════════════════════════════════════════════════
# HIGH-LEVEL API
# ══════════════════════════════════════════════════════════

def analyze_diff(diff_text: str) -> DiffSummary:
    """Full analysis pipeline for a unified diff.

    Args:
        diff_text: Raw unified diff text (from git log -p or git show).

    Returns:
        DiffSummary with files, symbols, shape, stats, and summary.
    """
    # Parse
    file_diffs = parse_unified_diff(diff_text)

    # Filter skippable files
    file_diffs = [fd for fd in file_diffs if not should_skip_file(fd.path)]

    # Classify symbols
    sym_added, sym_modified, sym_deleted = classify_symbols(file_diffs)

    # Classify shape
    shape = classify_change_shape(file_diffs, sym_added, sym_modified, sym_deleted)

    # Stats
    stats = {
        "files_changed": len(file_diffs),
        "insertions": sum(fd.insertions for fd in file_diffs if not fd.is_binary),
        "deletions": sum(fd.deletions for fd in file_diffs if not fd.is_binary),
    }

    # Summary
    summary = generate_summary(file_diffs, sym_added, sym_modified, sym_deleted, shape)

    return DiffSummary(
        files=file_diffs,
        symbols_added=sym_added,
        symbols_modified=sym_modified,
        symbols_deleted=sym_deleted,
        change_shape=shape,
        diff_stats=stats,
        summary_text=summary,
    )


def get_commit_diff(commit_hash: str, cwd: str = None) -> Optional[str]:
    """Get the unified diff for a single commit via git show."""
    try:
        result = subprocess.run(
            ["git", "show", "--format=", "--patch", commit_hash],
            capture_output=True, text=True, timeout=30,
            cwd=cwd or "."
        )
        if result.returncode == 0:
            return result.stdout
    except Exception:
        pass
    return None


def get_commits_with_diffs(
    max_commits: int = 20,
    since: str = None,
    cwd: str = None
) -> List[Tuple[str, str, str]]:
    """Get commits with their diffs via git log -p (single process, streaming).

    Returns: [(hash, subject, diff_text)] tuples.
    """
    cmd = [
        "git", "log",
        f"-{max_commits}",
        "--no-merges",
        "--format=COMMIT_START %H %s",
        "-p"
    ]
    if since:
        cmd.append(f"--since={since}")

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120,
            cwd=cwd or "."
        )
        if result.returncode != 0:
            return []
    except Exception:
        return []

    # Parse output: split by COMMIT_START markers
    commits = []
    current_hash = None
    current_subject = None
    current_diff_lines = []

    for line in result.stdout.split('\n'):
        if line.startswith('COMMIT_START '):
            # Save previous commit
            if current_hash:
                diff_text = '\n'.join(current_diff_lines)
                if diff_text.strip():
                    commits.append((current_hash, current_subject, diff_text))

            # Parse new commit
            parts = line.split(' ', 2)
            current_hash = parts[1] if len(parts) > 1 else ""
            current_subject = parts[2] if len(parts) > 2 else ""
            current_diff_lines = []
        else:
            current_diff_lines.append(line)

    # Save last commit
    if current_hash:
        diff_text = '\n'.join(current_diff_lines)
        if diff_text.strip():
            commits.append((current_hash, current_subject, diff_text))

    return commits


# ══════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════

if __name__ == "__main__":
    import json

    if len(sys.argv) < 2:
        print("Usage: diff_parser.py <commit_hash>")
        print("       diff_parser.py --stdin < diff.patch")
        sys.exit(1)

    if sys.argv[1] == "--stdin":
        diff_text = sys.stdin.read()
    else:
        diff_text = get_commit_diff(sys.argv[1])
        if not diff_text:
            print(f"Error: could not get diff for {sys.argv[1]}")
            sys.exit(1)

    result = analyze_diff(diff_text)

    print(f"Change shape: {result.change_shape}")
    print(f"Stats: {result.diff_stats}")
    print(f"Symbols added: {[f'{s.kind}:{s.name}' for s in result.symbols_added]}")
    print(f"Symbols modified: {[f'{s.kind}:{s.name}' for s in result.symbols_modified]}")
    print(f"Symbols deleted: {[f'{s.kind}:{s.name}' for s in result.symbols_deleted]}")
    print(f"\n--- Diff Summary ---")
    print(result.summary_text)
