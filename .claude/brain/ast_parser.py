#!/usr/bin/env python3
"""
ast_parser.py - Multi-language AST parser for code structure extraction

Extracts Module, Class, Function, and Interface nodes from source files.
Uses tree-sitter when available (30+ languages), falls back to regex
parsing (80% coverage, zero dependencies).

Usage (standalone test):
    python3 ast_parser.py .                    # Parse current directory
    python3 ast_parser.py ./src --lang py,ts   # Specific dir + languages
    python3 ast_parser.py --dry-run ./src      # Preview without output
"""

import hashlib
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple

# ══════════════════════════════════════════════════════════
# TREE-SITTER SETUP
# ══════════════════════════════════════════════════════════

HAS_TREE_SITTER = False

try:
    from tree_sitter_languages import get_parser as ts_get_parser, get_language as ts_get_language
    HAS_TREE_SITTER = True
except ImportError:
    pass


# ══════════════════════════════════════════════════════════
# DATA STRUCTURES
# ══════════════════════════════════════════════════════════

@dataclass
class ModuleInfo:
    """Parsed module (file) information."""
    file_path: str
    language: str
    line_count: int
    import_count: int
    symbol_count: int
    body_hash: str  # md5 of file content for skip-on-rerun
    imports: List[str] = field(default_factory=list)  # imported module names


@dataclass
class ClassInfo:
    """Parsed class/struct information."""
    file_path: str
    language: str
    name: str
    qualified_name: str  # module.ClassName
    line_start: int
    line_end: int
    docstring: str = ""
    base_classes: List[str] = field(default_factory=list)
    detected_pattern: str = ""  # Controller, Service, Repository, etc.
    methods: List[str] = field(default_factory=list)  # method names


@dataclass
class FunctionInfo:
    """Parsed function/method information."""
    file_path: str
    language: str
    name: str
    qualified_name: str  # module.ClassName.method or module.func
    signature: str
    line_start: int
    line_end: int
    docstring: str = ""
    is_method: bool = False
    param_count: int = 0
    complexity_hint: str = "simple"  # simple, moderate, complex


@dataclass
class InterfaceInfo:
    """Parsed interface/trait/protocol information."""
    file_path: str
    language: str
    name: str
    qualified_name: str
    line_start: int
    line_end: int
    method_signatures: List[str] = field(default_factory=list)


@dataclass
class ParseResult:
    """Complete parse result for a single file."""
    module: ModuleInfo
    classes: List[ClassInfo] = field(default_factory=list)
    functions: List[FunctionInfo] = field(default_factory=list)
    interfaces: List[InterfaceInfo] = field(default_factory=list)


# ══════════════════════════════════════════════════════════
# LANGUAGE DETECTION
# ══════════════════════════════════════════════════════════

LANG_MAP = {
    '.py': 'python',
    '.js': 'javascript',
    '.jsx': 'javascript',
    '.ts': 'typescript',
    '.tsx': 'typescript',
    '.rb': 'ruby',
    '.go': 'go',
    '.java': 'java',
    '.rs': 'rust',
    '.php': 'php',
}

# Tree-sitter language name mapping
TS_LANG_MAP = {
    'python': 'python',
    'javascript': 'javascript',
    'typescript': 'typescript',
    'ruby': 'ruby',
    'go': 'go',
    'java': 'java',
    'rust': 'rust',
    'php': 'php',
}

# Directories to always skip
SKIP_DIRS = {
    'node_modules', 'vendor', '.venv', 'venv', '__pycache__',
    '.git', 'dist', 'build', '.next', '.nuxt', 'coverage',
    '.tox', '.mypy_cache', '.pytest_cache', 'target', '.gradle',
    'bin', 'obj', '.idea', '.vscode', '.claude',
}

MAX_FILE_SIZE = 500 * 1024  # 500KB


def detect_language(file_path: str) -> Optional[str]:
    """Detect programming language from file extension."""
    ext = Path(file_path).suffix.lower()
    return LANG_MAP.get(ext)


def should_skip_path(path: Path) -> bool:
    """Check if a path should be skipped."""
    for part in path.parts:
        if part in SKIP_DIRS or part.startswith('.'):
            return True
    return False


def compute_body_hash(content: str) -> str:
    """Compute MD5 hash of file content for change detection."""
    return hashlib.md5(content.encode('utf-8', errors='ignore')).hexdigest()


# ══════════════════════════════════════════════════════════
# PATTERN DETECTION
# ══════════════════════════════════════════════════════════

ARCHITECTURAL_PATTERNS = {
    r'Controller$': 'Controller',
    r'Service$': 'Service',
    r'Repository$': 'Repository',
    r'Factory$': 'Factory',
    r'Builder$': 'Builder',
    r'Adapter$': 'Adapter',
    r'Strategy$': 'Strategy',
    r'Observer$': 'Observer',
    r'Handler$': 'Handler',
    r'Middleware$': 'Middleware',
    r'Validator$': 'Validator',
    r'Serializer$': 'Serializer',
    r'Presenter$': 'Presenter',
    r'ViewModel$': 'ViewModel',
    r'UseCase$': 'UseCase',
    r'Interactor$': 'Interactor',
    r'Provider$': 'Provider',
    r'Manager$': 'Manager',
    r'Client$': 'Client',
    r'Gateway$': 'Gateway',
    r'Command$': 'Command',
    r'Query$': 'Query',
    r'Event$': 'Event',
    r'Listener$': 'Listener',
    r'Subscriber$': 'Subscriber',
    r'DTO$': 'DTO',
    r'Model$': 'Model',
    r'Entity$': 'Entity',
    r'Spec$': 'Test',
    r'Test$': 'Test',
    r'Mock$': 'Test',
}


def detect_pattern(name: str) -> str:
    """Detect architectural pattern from class name."""
    for pattern, label in ARCHITECTURAL_PATTERNS.items():
        if re.search(pattern, name):
            return label
    return ""


def estimate_complexity(lines: List[str]) -> str:
    """Estimate function complexity from its body lines.

    Simple heuristic:
    - Count branches (if/elif/else/case/match/for/while/try/catch)
    - Count max nesting depth
    """
    branch_count = 0
    max_nesting = 0
    current_nesting = 0

    branch_patterns = re.compile(
        r'^\s*(if|elif|else|case|match|for|while|try|catch|except|rescue)\b'
    )

    for line in lines:
        stripped = line.lstrip()
        if branch_patterns.match(stripped):
            branch_count += 1

        # Estimate nesting by indentation change
        indent = len(line) - len(stripped) if stripped else 0
        nesting = indent // 4  # rough estimate
        if nesting > current_nesting:
            current_nesting = nesting
        max_nesting = max(max_nesting, current_nesting)

    if branch_count <= 2 and max_nesting <= 2:
        return "simple"
    elif branch_count <= 5 and max_nesting <= 3:
        return "moderate"
    else:
        return "complex"


# ══════════════════════════════════════════════════════════
# REGEX FALLBACK PARSER
# ══════════════════════════════════════════════════════════

def _parse_python_regex(content: str, file_path: str) -> ParseResult:
    """Parse Python file using regex (fallback)."""
    lines = content.split('\n')
    module_name = Path(file_path).stem
    body_hash = compute_body_hash(content)

    imports = []
    classes = []
    functions = []
    current_class = None
    current_class_indent = 0

    # Count imports
    for line in lines:
        m = re.match(r'^(?:from\s+(\S+)\s+)?import\s+(.+)', line)
        if m:
            mod = m.group(1) or m.group(2).split(',')[0].strip().split('.')[0]
            imports.append(mod)

    # Parse classes and functions
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        indent = len(line) - len(stripped)

        # Check if we've left the current class scope
        if current_class and indent <= current_class_indent and stripped and not stripped.startswith('#'):
            current_class = None

        # Class definition
        cls_match = re.match(r'^(\s*)class\s+(\w+)(?:\(([^)]*)\))?:', line)
        if cls_match:
            name = cls_match.group(2)
            bases = [b.strip() for b in (cls_match.group(3) or "").split(',') if b.strip()]

            # Find class end (next line at same or lower indent, or EOF)
            class_end = len(lines)
            class_indent = len(cls_match.group(1))
            for j in range(i + 1, len(lines)):
                next_stripped = lines[j].lstrip()
                next_indent = len(lines[j]) - len(next_stripped)
                if next_stripped and not next_stripped.startswith('#') and next_indent <= class_indent:
                    class_end = j
                    break

            # Docstring
            docstring = ""
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line.startswith('"""') or next_line.startswith("'''"):
                    doc_lines = []
                    quote = next_line[:3]
                    if next_line.count(quote) >= 2:
                        docstring = next_line.strip(quote).strip()
                    else:
                        for k in range(i + 1, min(i + 10, len(lines))):
                            doc_lines.append(lines[k].strip())
                            if lines[k].strip().endswith(quote) and k > i + 1:
                                break
                        docstring = ' '.join(doc_lines).strip(quote).strip()

            cls_info = ClassInfo(
                file_path=file_path,
                language="python",
                name=name,
                qualified_name=f"{module_name}.{name}",
                line_start=i + 1,
                line_end=class_end,
                docstring=docstring[:200],
                base_classes=bases,
                detected_pattern=detect_pattern(name),
            )
            classes.append(cls_info)
            current_class = cls_info
            current_class_indent = class_indent
            continue

        # Function/method definition
        fn_match = re.match(r'^(\s*)(?:async\s+)?def\s+(\w+)\s*\(([^)]*)\)', line)
        if fn_match:
            fn_indent = len(fn_match.group(1))
            name = fn_match.group(2)
            params_str = fn_match.group(3)
            params = [p.strip().split(':')[0].split('=')[0].strip() for p in params_str.split(',') if p.strip()]
            params = [p for p in params if p and p != 'self' and p != 'cls']

            is_method = current_class is not None and fn_indent > current_class_indent
            if is_method:
                qualified = f"{module_name}.{current_class.name}.{name}"
                current_class.methods.append(name)
            else:
                qualified = f"{module_name}.{name}"

            # Find function end
            fn_end = len(lines)
            for j in range(i + 1, len(lines)):
                next_stripped = lines[j].lstrip()
                next_indent = len(lines[j]) - len(next_stripped)
                if next_stripped and not next_stripped.startswith('#') and next_indent <= fn_indent:
                    fn_end = j
                    break

            # Docstring
            docstring = ""
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line.startswith('"""') or next_line.startswith("'''"):
                    quote = next_line[:3]
                    if next_line.count(quote) >= 2:
                        docstring = next_line.strip(quote).strip()
                    else:
                        doc_parts = []
                        for k in range(i + 1, min(i + 10, len(lines))):
                            doc_parts.append(lines[k].strip())
                            if lines[k].strip().endswith(quote) and k > i + 1:
                                break
                        docstring = ' '.join(doc_parts).strip(quote).strip()

            # Complexity
            body_lines = lines[i + 1:fn_end]
            complexity = estimate_complexity(body_lines)

            # Signature
            sig = f"def {name}({params_str.strip()})"
            if 'async def' in line:
                sig = f"async {sig}"

            functions.append(FunctionInfo(
                file_path=file_path,
                language="python",
                name=name,
                qualified_name=qualified,
                signature=sig[:200],
                line_start=i + 1,
                line_end=fn_end,
                docstring=docstring[:200],
                is_method=is_method,
                param_count=len(params),
                complexity_hint=complexity,
            ))

    module = ModuleInfo(
        file_path=file_path,
        language="python",
        line_count=len(lines),
        import_count=len(imports),
        symbol_count=len(classes) + len(functions),
        body_hash=body_hash,
        imports=imports,
    )

    return ParseResult(module=module, classes=classes, functions=functions)


def _parse_js_ts_regex(content: str, file_path: str, language: str) -> ParseResult:
    """Parse JavaScript/TypeScript file using regex (fallback)."""
    lines = content.split('\n')
    module_name = Path(file_path).stem
    body_hash = compute_body_hash(content)

    imports = []
    classes = []
    functions = []
    interfaces = []

    # Count imports
    for line in lines:
        m = re.match(r'^import\s+.*?from\s+[\'"]([^\'"]+)[\'"]', line)
        if m:
            imports.append(m.group(1))
        m = re.match(r'^(?:const|let|var)\s+\w+\s*=\s*require\([\'"]([^\'"]+)[\'"]\)', line)
        if m:
            imports.append(m.group(1))

    for i, line in enumerate(lines):
        stripped = line.lstrip()

        # Class
        cls_match = re.match(
            r'^(?:export\s+)?(?:default\s+)?(?:abstract\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([^{]+))?',
            stripped
        )
        if cls_match:
            name = cls_match.group(1)
            bases = []
            if cls_match.group(2):
                bases.append(cls_match.group(2))
            # Find class end (matching brace)
            class_end = _find_brace_end(lines, i)
            classes.append(ClassInfo(
                file_path=file_path,
                language=language,
                name=name,
                qualified_name=f"{module_name}.{name}",
                line_start=i + 1,
                line_end=class_end,
                base_classes=bases,
                detected_pattern=detect_pattern(name),
            ))
            continue

        # Interface (TypeScript)
        if language == 'typescript':
            iface_match = re.match(r'^(?:export\s+)?interface\s+(\w+)', stripped)
            if iface_match:
                name = iface_match.group(1)
                iface_end = _find_brace_end(lines, i)
                interfaces.append(InterfaceInfo(
                    file_path=file_path,
                    language=language,
                    name=name,
                    qualified_name=f"{module_name}.{name}",
                    line_start=i + 1,
                    line_end=iface_end,
                ))
                continue

            type_match = re.match(r'^(?:export\s+)?type\s+(\w+)\s*=', stripped)
            if type_match:
                name = type_match.group(1)
                interfaces.append(InterfaceInfo(
                    file_path=file_path,
                    language=language,
                    name=name,
                    qualified_name=f"{module_name}.{name}",
                    line_start=i + 1,
                    line_end=i + 1,
                ))
                continue

        # Function declarations
        fn_match = re.match(
            r'^(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)',
            stripped
        )
        if fn_match:
            name = fn_match.group(1)
            params_str = fn_match.group(2)
            params = [p.strip().split(':')[0].split('=')[0].strip() for p in params_str.split(',') if p.strip()]
            fn_end = _find_brace_end(lines, i)
            body_lines = lines[i + 1:fn_end]
            functions.append(FunctionInfo(
                file_path=file_path,
                language=language,
                name=name,
                qualified_name=f"{module_name}.{name}",
                signature=f"function {name}({params_str.strip()[:100]})",
                line_start=i + 1,
                line_end=fn_end,
                param_count=len(params),
                complexity_hint=estimate_complexity(body_lines),
            ))
            continue

        # Arrow functions / const functions
        arrow_match = re.match(
            r'^(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:\([^)]*\)|[^=])\s*=>',
            stripped
        )
        if arrow_match:
            name = arrow_match.group(1)
            fn_end = _find_brace_end(lines, i) if '{' in line else i + 1
            functions.append(FunctionInfo(
                file_path=file_path,
                language=language,
                name=name,
                qualified_name=f"{module_name}.{name}",
                signature=f"const {name} = (...) =>",
                line_start=i + 1,
                line_end=fn_end,
            ))

    module = ModuleInfo(
        file_path=file_path,
        language=language,
        line_count=len(lines),
        import_count=len(imports),
        symbol_count=len(classes) + len(functions) + len(interfaces),
        body_hash=body_hash,
        imports=imports,
    )

    return ParseResult(module=module, classes=classes, functions=functions, interfaces=interfaces)


def _parse_generic_regex(content: str, file_path: str, language: str) -> ParseResult:
    """Generic regex parser for Go, Ruby, Java, Rust, PHP."""
    lines = content.split('\n')
    module_name = Path(file_path).stem
    body_hash = compute_body_hash(content)

    imports = []
    classes = []
    functions = []
    interfaces = []

    # Language-specific patterns
    if language == 'go':
        import_pattern = re.compile(r'^\s*"([^"]+)"')
        func_pattern = re.compile(r'^func\s+(?:\(\w+\s+\*?(\w+)\)\s+)?(\w+)\s*\(([^)]*)\)')
        struct_pattern = re.compile(r'^type\s+(\w+)\s+struct\b')
        iface_pattern = re.compile(r'^type\s+(\w+)\s+interface\b')
    elif language == 'ruby':
        import_pattern = re.compile(r'^require\s+[\'"]([^\'"]+)[\'"]')
        func_pattern = re.compile(r'^\s*def\s+(\w+[?!]?)\s*(?:\(([^)]*)\))?')
        struct_pattern = re.compile(r'^\s*(?:class|module)\s+(\w+)(?:\s*<\s*(\w+))?')
        iface_pattern = None
    elif language == 'java':
        import_pattern = re.compile(r'^import\s+(?:static\s+)?([^;]+);')
        func_pattern = re.compile(r'^\s*(?:public|private|protected|static|final|abstract|\s)*\s+\w+\s+(\w+)\s*\(([^)]*)\)')
        struct_pattern = re.compile(r'^\s*(?:public|private|protected|abstract|final|\s)*\s*class\s+(\w+)(?:\s+extends\s+(\w+))?')
        iface_pattern = re.compile(r'^\s*(?:public\s+)?interface\s+(\w+)')
    elif language == 'rust':
        import_pattern = re.compile(r'^use\s+([^;]+);')
        func_pattern = re.compile(r'^\s*(?:pub\s+)?(?:async\s+)?fn\s+(\w+)\s*(?:<[^>]*>)?\s*\(([^)]*)\)')
        struct_pattern = re.compile(r'^\s*(?:pub\s+)?(?:struct|enum)\s+(\w+)')
        iface_pattern = re.compile(r'^\s*(?:pub\s+)?trait\s+(\w+)')
    elif language == 'php':
        import_pattern = re.compile(r'^use\s+([^;]+);')
        func_pattern = re.compile(r'^\s*(?:public|private|protected|static|\s)*\s*function\s+(\w+)\s*\(([^)]*)\)')
        struct_pattern = re.compile(r'^\s*(?:abstract\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?')
        iface_pattern = re.compile(r'^\s*interface\s+(\w+)')
    else:
        import_pattern = None
        func_pattern = None
        struct_pattern = None
        iface_pattern = None

    for i, line in enumerate(lines):
        stripped = line.lstrip()

        if import_pattern:
            m = import_pattern.match(stripped)
            if m:
                imports.append(m.group(1))
                continue

        if struct_pattern:
            m = struct_pattern.match(stripped)
            if m:
                name = m.group(1)
                bases = [m.group(2)] if m.lastindex >= 2 and m.group(2) else []
                class_end = _find_brace_end(lines, i) if language != 'ruby' else _find_ruby_end(lines, i)
                classes.append(ClassInfo(
                    file_path=file_path,
                    language=language,
                    name=name,
                    qualified_name=f"{module_name}.{name}",
                    line_start=i + 1,
                    line_end=class_end,
                    base_classes=bases,
                    detected_pattern=detect_pattern(name),
                ))
                continue

        if iface_pattern:
            m = iface_pattern.match(stripped)
            if m:
                name = m.group(1)
                iface_end = _find_brace_end(lines, i) if language != 'ruby' else i + 1
                interfaces.append(InterfaceInfo(
                    file_path=file_path,
                    language=language,
                    name=name,
                    qualified_name=f"{module_name}.{name}",
                    line_start=i + 1,
                    line_end=iface_end,
                ))
                continue

        if func_pattern:
            m = func_pattern.match(stripped)
            if m:
                # Go: receiver type is group 1 if present, function name is group 2
                if language == 'go' and m.lastindex >= 2:
                    receiver = m.group(1)
                    name = m.group(2)
                    params_str = m.group(3) if m.lastindex >= 3 else ""
                    is_method = receiver is not None
                    qualified = f"{module_name}.{receiver}.{name}" if receiver else f"{module_name}.{name}"
                elif language == 'ruby':
                    name = m.group(1)
                    params_str = m.group(2) if m.lastindex >= 2 and m.group(2) else ""
                    is_method = False
                    qualified = f"{module_name}.{name}"
                else:
                    name = m.group(1)
                    params_str = m.group(2) if m.lastindex >= 2 and m.group(2) else ""
                    is_method = False
                    qualified = f"{module_name}.{name}"

                params = [p.strip().split(':')[0].split('=')[0].strip() for p in params_str.split(',') if p.strip()] if params_str else []
                fn_end = _find_brace_end(lines, i) if language != 'ruby' else _find_ruby_end(lines, i)

                functions.append(FunctionInfo(
                    file_path=file_path,
                    language=language,
                    name=name,
                    qualified_name=qualified,
                    signature=stripped[:200],
                    line_start=i + 1,
                    line_end=fn_end,
                    is_method=is_method,
                    param_count=len(params),
                ))

    module = ModuleInfo(
        file_path=file_path,
        language=language,
        line_count=len(lines),
        import_count=len(imports),
        symbol_count=len(classes) + len(functions) + len(interfaces),
        body_hash=body_hash,
        imports=imports,
    )

    return ParseResult(module=module, classes=classes, functions=functions, interfaces=interfaces)


def _find_brace_end(lines: List[str], start: int) -> int:
    """Find matching closing brace for C-family languages."""
    depth = 0
    found_open = False
    for i in range(start, min(start + 2000, len(lines))):
        for ch in lines[i]:
            if ch == '{':
                depth += 1
                found_open = True
            elif ch == '}':
                depth -= 1
                if found_open and depth == 0:
                    return i + 1
    return min(start + 50, len(lines))


def _find_ruby_end(lines: List[str], start: int) -> int:
    """Find matching 'end' for Ruby/Python-like blocks."""
    depth = 0
    for i in range(start, min(start + 2000, len(lines))):
        stripped = lines[i].lstrip()
        if re.match(r'^(def|class|module|do|if|unless|case|begin|while|until|for)\b', stripped):
            depth += 1
        if stripped == 'end' or stripped.startswith('end '):
            depth -= 1
            if depth <= 0:
                return i + 1
    return min(start + 50, len(lines))


# ══════════════════════════════════════════════════════════
# TREE-SITTER PARSER
# ══════════════════════════════════════════════════════════

def _parse_with_tree_sitter(content: str, file_path: str, language: str) -> Optional[ParseResult]:
    """Parse file using tree-sitter. Returns None if language not supported."""
    if not HAS_TREE_SITTER:
        return None

    ts_lang = TS_LANG_MAP.get(language)
    if not ts_lang:
        return None

    try:
        parser = ts_get_parser(ts_lang)
    except Exception:
        return None

    tree = parser.parse(content.encode('utf-8'))
    root = tree.root_node

    lines = content.split('\n')
    module_name = Path(file_path).stem
    body_hash = compute_body_hash(content)

    classes = []
    functions = []
    interfaces = []
    imports = []

    def _get_text(node) -> str:
        return content[node.start_byte:node.end_byte]

    def _get_docstring(node) -> str:
        """Try to extract docstring from first child."""
        for child in node.children:
            if child.type in ('expression_statement', 'comment', 'string'):
                text = _get_text(child).strip()
                if text.startswith('"""') or text.startswith("'''"):
                    return text.strip('"').strip("'").strip()[:200]
                if text.startswith('//') or text.startswith('#'):
                    return text.lstrip('/#').strip()[:200]
            # Python: block > expression_statement > string
            if child.type == 'block':
                for sub in child.children:
                    if sub.type == 'expression_statement':
                        for subsub in sub.children:
                            if subsub.type == 'string':
                                text = _get_text(subsub).strip('"').strip("'").strip()
                                return text[:200]
                break  # only check first meaningful child
        return ""

    def _walk(node, class_name: str = None):
        """Walk AST tree and extract symbols."""
        ntype = node.type

        # Python
        if ntype == 'import_statement' or ntype == 'import_from_statement':
            imports.append(_get_text(node).split()[-1].split('.')[0])
        elif ntype == 'class_definition':
            name_node = node.child_by_field_name('name')
            name = _get_text(name_node) if name_node else ""
            bases = []
            args_node = node.child_by_field_name('superclasses')
            if args_node:
                for child in args_node.children:
                    if child.type == 'identifier' or child.type == 'attribute':
                        bases.append(_get_text(child))

            cls = ClassInfo(
                file_path=file_path, language=language, name=name,
                qualified_name=f"{module_name}.{name}",
                line_start=node.start_point[0] + 1,
                line_end=node.end_point[0] + 1,
                docstring=_get_docstring(node),
                base_classes=bases,
                detected_pattern=detect_pattern(name),
            )
            classes.append(cls)
            # Walk children with class context
            for child in node.children:
                _walk(child, class_name=name)
            return

        elif ntype == 'function_definition':
            name_node = node.child_by_field_name('name')
            name = _get_text(name_node) if name_node else ""
            params_node = node.child_by_field_name('parameters')
            params_str = _get_text(params_node) if params_node else "()"
            params = [p.strip().split(':')[0].split('=')[0].strip()
                      for p in params_str.strip('()').split(',') if p.strip()]
            params = [p for p in params if p and p != 'self' and p != 'cls']

            is_method = class_name is not None
            if is_method:
                qualified = f"{module_name}.{class_name}.{name}"
            else:
                qualified = f"{module_name}.{name}"

            # Get body for complexity
            body_start = node.start_point[0] + 1
            body_end = node.end_point[0] + 1
            body_lines = lines[body_start:body_end]

            functions.append(FunctionInfo(
                file_path=file_path, language=language, name=name,
                qualified_name=qualified,
                signature=f"def {name}{params_str}"[:200],
                line_start=node.start_point[0] + 1,
                line_end=node.end_point[0] + 1,
                docstring=_get_docstring(node),
                is_method=is_method,
                param_count=len(params),
                complexity_hint=estimate_complexity(body_lines),
            ))
            return  # don't recurse into function body

        # JS/TS specific
        elif ntype == 'class_declaration':
            name_node = node.child_by_field_name('name')
            name = _get_text(name_node) if name_node else ""
            classes.append(ClassInfo(
                file_path=file_path, language=language, name=name,
                qualified_name=f"{module_name}.{name}",
                line_start=node.start_point[0] + 1,
                line_end=node.end_point[0] + 1,
                detected_pattern=detect_pattern(name),
            ))
            for child in node.children:
                _walk(child, class_name=name)
            return

        elif ntype in ('function_declaration', 'method_definition'):
            name_node = node.child_by_field_name('name')
            name = _get_text(name_node) if name_node else ""
            params_node = node.child_by_field_name('parameters')
            params_str = _get_text(params_node) if params_node else "()"

            is_method = class_name is not None
            qualified = f"{module_name}.{class_name}.{name}" if is_method else f"{module_name}.{name}"

            functions.append(FunctionInfo(
                file_path=file_path, language=language, name=name,
                qualified_name=qualified,
                signature=f"function {name}{params_str}"[:200],
                line_start=node.start_point[0] + 1,
                line_end=node.end_point[0] + 1,
                is_method=is_method,
            ))
            return

        elif ntype == 'interface_declaration':
            name_node = node.child_by_field_name('name')
            name = _get_text(name_node) if name_node else ""
            interfaces.append(InterfaceInfo(
                file_path=file_path, language=language, name=name,
                qualified_name=f"{module_name}.{name}",
                line_start=node.start_point[0] + 1,
                line_end=node.end_point[0] + 1,
            ))
            return

        # Go specific
        elif ntype == 'function_declaration' and language == 'go':
            name_node = node.child_by_field_name('name')
            name = _get_text(name_node) if name_node else ""
            functions.append(FunctionInfo(
                file_path=file_path, language=language, name=name,
                qualified_name=f"{module_name}.{name}",
                signature=_get_text(node).split('{')[0].strip()[:200],
                line_start=node.start_point[0] + 1,
                line_end=node.end_point[0] + 1,
            ))
            return

        elif ntype == 'type_declaration' and language == 'go':
            for child in node.children:
                if child.type == 'type_spec':
                    name_node = child.child_by_field_name('name')
                    type_node = child.child_by_field_name('type')
                    if name_node:
                        name = _get_text(name_node)
                        if type_node and type_node.type == 'struct_type':
                            classes.append(ClassInfo(
                                file_path=file_path, language=language, name=name,
                                qualified_name=f"{module_name}.{name}",
                                line_start=child.start_point[0] + 1,
                                line_end=child.end_point[0] + 1,
                                detected_pattern=detect_pattern(name),
                            ))
                        elif type_node and type_node.type == 'interface_type':
                            interfaces.append(InterfaceInfo(
                                file_path=file_path, language=language, name=name,
                                qualified_name=f"{module_name}.{name}",
                                line_start=child.start_point[0] + 1,
                                line_end=child.end_point[0] + 1,
                            ))
            return

        # Recurse children
        for child in node.children:
            _walk(child, class_name=class_name)

    _walk(root)

    module = ModuleInfo(
        file_path=file_path, language=language,
        line_count=len(lines), import_count=len(imports),
        symbol_count=len(classes) + len(functions) + len(interfaces),
        body_hash=body_hash, imports=imports,
    )

    return ParseResult(module=module, classes=classes, functions=functions, interfaces=interfaces)


# ══════════════════════════════════════════════════════════
# HIGH-LEVEL API
# ══════════════════════════════════════════════════════════

def parse_file(file_path: str, content: str = None) -> Optional[ParseResult]:
    """Parse a single file and return structured code information.

    Uses tree-sitter if available, falls back to regex.
    Returns None if language is not supported.
    """
    language = detect_language(file_path)
    if not language:
        return None

    if content is None:
        try:
            content = Path(file_path).read_text(encoding='utf-8', errors='ignore')
        except Exception:
            return None

    if len(content) > MAX_FILE_SIZE:
        return None

    # Try tree-sitter first
    result = _parse_with_tree_sitter(content, file_path, language)
    if result:
        return result

    # Fallback to regex
    if language == 'python':
        return _parse_python_regex(content, file_path)
    elif language in ('javascript', 'typescript'):
        return _parse_js_ts_regex(content, file_path, language)
    else:
        return _parse_generic_regex(content, file_path, language)


def scan_directory(
    root_dir: str,
    languages: Set[str] = None,
    existing_hashes: Dict[str, str] = None
) -> List[ParseResult]:
    """Scan a directory and parse all supported files.

    Args:
        root_dir: Root directory to scan.
        languages: Optional set of languages to filter (e.g. {"python", "typescript"}).
        existing_hashes: {file_path: body_hash} for skip-on-rerun optimization.

    Returns:
        List of ParseResult for each parsed file.
    """
    root = Path(root_dir).resolve()
    existing_hashes = existing_hashes or {}
    results = []

    for path in sorted(root.rglob('*')):
        if not path.is_file():
            continue

        # Convert to relative path
        try:
            rel_path = str(path.relative_to(Path('.').resolve()))
        except ValueError:
            rel_path = str(path)

        # Skip check
        if should_skip_path(path):
            continue

        language = detect_language(str(path))
        if not language:
            continue
        if languages and language not in languages:
            continue

        # Size check
        try:
            size = path.stat().st_size
            if size > MAX_FILE_SIZE or size == 0:
                continue
        except OSError:
            continue

        # Read content
        try:
            content = path.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue

        # Skip-on-rerun: check body_hash
        body_hash = compute_body_hash(content)
        if rel_path in existing_hashes and existing_hashes[rel_path] == body_hash:
            continue

        result = parse_file(rel_path, content)
        if result:
            results.append(result)

    return results


def generate_node_id(file_path: str, qualified_name: str, label: str) -> str:
    """Generate deterministic 16-char hex node ID for Code nodes.

    ID = md5(file_path:qualified_name|label)[:16]
    """
    source = f"{file_path}:{qualified_name}|{label}"
    return hashlib.md5(source.encode()).hexdigest()[:16]


def generate_content_text(item) -> str:
    """Generate compact content text for embedding (~200-500 tokens).

    Format varies by type:
    - Function: signature, location, docstring, complexity
    - Class: name, location, bases, pattern, methods
    - Module: path, language, stats, imports
    """
    if isinstance(item, FunctionInfo):
        lines_span = item.line_end - item.line_start
        parts = [item.signature]
        parts.append(f"  File: {item.file_path}:{item.line_start}-{item.line_end} ({lines_span} lines)")
        if item.docstring:
            parts.append(f"  Docstring: {item.docstring}")
        parts.append(f"  Complexity: {item.complexity_hint}")
        if item.is_method:
            parts.append(f"  Method of: {item.qualified_name.rsplit('.', 1)[0]}")
        return '\n'.join(parts)

    elif isinstance(item, ClassInfo):
        lines_span = item.line_end - item.line_start
        parts = [f"class {item.name}"]
        parts.append(f"  File: {item.file_path}:{item.line_start}-{item.line_end} ({lines_span} lines)")
        if item.docstring:
            parts.append(f"  Docstring: {item.docstring}")
        if item.base_classes:
            parts.append(f"  Inherits: {', '.join(item.base_classes)}")
        if item.detected_pattern:
            parts.append(f"  Pattern: {item.detected_pattern}")
        if item.methods:
            parts.append(f"  Methods: {', '.join(item.methods[:10])}")
        return '\n'.join(parts)

    elif isinstance(item, InterfaceInfo):
        parts = [f"interface {item.name}"]
        parts.append(f"  File: {item.file_path}:{item.line_start}-{item.line_end}")
        if item.method_signatures:
            parts.append(f"  Methods: {', '.join(item.method_signatures[:10])}")
        return '\n'.join(parts)

    elif isinstance(item, ModuleInfo):
        parts = [f"module {Path(item.file_path).stem}"]
        parts.append(f"  File: {item.file_path} ({item.line_count} lines, {item.language})")
        parts.append(f"  Symbols: {item.symbol_count}, Imports: {item.import_count}")
        if item.imports:
            parts.append(f"  Imports: {', '.join(item.imports[:10])}")
        return '\n'.join(parts)

    return str(item)


# ══════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════

if __name__ == "__main__":
    import json

    dry_run = "--dry-run" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith('--')]

    root_dir = args[0] if args else "."
    languages = None

    # Parse --lang flag
    for i, a in enumerate(sys.argv):
        if a == '--lang' and i + 1 < len(sys.argv):
            lang_filter = sys.argv[i + 1].split(',')
            # Map short names to full names
            short_map = {'py': 'python', 'js': 'javascript', 'ts': 'typescript', 'rb': 'ruby'}
            languages = {short_map.get(l, l) for l in lang_filter}

    print(f"Scanning {root_dir}" + (f" (languages: {languages})" if languages else ""))
    if HAS_TREE_SITTER:
        print("Using: tree-sitter")
    else:
        print("Using: regex fallback (install tree-sitter-languages for better parsing)")

    results = scan_directory(root_dir, languages=languages)

    total_modules = 0
    total_classes = 0
    total_functions = 0
    total_interfaces = 0

    for result in results:
        total_modules += 1
        total_classes += len(result.classes)
        total_functions += len(result.functions)
        total_interfaces += len(result.interfaces)

        if not dry_run:
            print(f"\n  Module: {result.module.file_path} ({result.module.language}, {result.module.line_count} lines)")
            for cls in result.classes:
                print(f"    Class: {cls.name} ({cls.line_start}-{cls.line_end})" +
                      (f" [{cls.detected_pattern}]" if cls.detected_pattern else ""))
            for fn in result.functions:
                method_marker = " [method]" if fn.is_method else ""
                print(f"    Function: {fn.name} ({fn.line_start}-{fn.line_end}){method_marker} [{fn.complexity_hint}]")
            for iface in result.interfaces:
                print(f"    Interface: {iface.name} ({iface.line_start}-{iface.line_end})")

    print(f"\nTotal: {total_modules} modules, {total_classes} classes, "
          f"{total_functions} functions, {total_interfaces} interfaces")
