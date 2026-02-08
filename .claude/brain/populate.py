#!/usr/bin/env python3
"""
populate.py - Popular o cérebro com conhecimento existente

Processa:
1. ADRs do ADR_LOG.md
2. DOMAIN.md (glossário e regras)
3. PATTERNS.md
4. EXPERIENCE_LIBRARY.md
5. Commits do git log

Uso:
    python populate.py all              # Processa tudo
    python populate.py adrs             # Só ADRs
    python populate.py domain           # Só domínio
    python populate.py commits [N]      # Últimos N commits (default: 7000)
"""

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Adiciona diretório atual ao path
sys.path.insert(0, str(Path(__file__).parent))

from brain_sqlite import BrainSQLite as Brain
from brain import get_current_developer


def parse_adr_log(content: str) -> List[Dict]:
    """Extrai ADRs do ADR_LOG.md.

    Handles two formats:
    - Block: ### Contexto\\n...text...\\n### Decisão\\n...
    - Compact: **Contexto**: inline text\\n**Decisão**: inline text\\n
    """
    adrs = []

    # Split by ADR headers (handles files with or without --- separators)
    sections = re.split(r'\n(?=## ADR-\d+)', content)

    for section in sections:
        match = re.search(r'## (ADR-\d+): (.+)', section)
        if not match:
            continue

        adr_id = match.group(1)
        title = match.group(2).strip()

        # Extrai data
        date_match = re.search(r'\*\*Data\*\*: (.+)', section)
        date = date_match.group(1).strip() if date_match else datetime.now().strftime("%Y-%m-%d")

        # Extrai status
        status_match = re.search(r'\*\*Status\*\*: (.+)', section)
        status = status_match.group(1).strip() if status_match else "Aceito"

        # Extrai contexto — block format then compact fallback
        context_match = re.search(r'### Contexto\n(.+?)(?:\n###|\n## |\Z)', section, re.DOTALL)
        if not context_match:
            context_match = re.search(r'\*\*Contexto\*\*[:\s]+(.+?)(?=\n\*\*[A-Z]|\n## |\Z)', section, re.DOTALL)
        context = context_match.group(1).strip() if context_match else ""

        # Extrai decisão — block format then compact fallback
        decision_match = re.search(r'### Decis[ãa]o\n(.+?)(?:\n###|\n## |\Z)', section, re.DOTALL)
        if not decision_match:
            decision_match = re.search(r'\*\*Decis[ãa]o\*\*[:\s]+(.+?)(?=\n\*\*[A-Z]|\n## |\Z)', section, re.DOTALL)
        decision = decision_match.group(1).strip() if decision_match else ""

        # Extrai consequências — block format then compact fallback
        conseq_match = re.search(r'### Consequ[êe]ncias\n(.+?)(?:\n---|\n## |\Z)', section, re.DOTALL)
        if not conseq_match:
            conseq_match = re.search(r'\*\*Consequ[êe]ncias\*\*[:\s]*\n?(.+?)(?=\n\*\*[A-Z]|\n## |\Z)', section, re.DOTALL)
        consequences = conseq_match.group(1).strip() if conseq_match else ""

        adrs.append({
            "id": adr_id,
            "title": title,
            "date": date,
            "status": status,
            "context": context,
            "decision": decision,
            "consequences": consequences,
            "full_content": section
        })

    return adrs


def parse_domain(content: str) -> List[Dict]:
    """Extrai conceitos do DOMAIN.md"""
    concepts = []

    # Extrai glossário
    glossary_match = re.search(r'## Glossário.*?\n(.+?)(?:\n## |$)', content, re.DOTALL)
    if glossary_match:
        glossary = glossary_match.group(1)

        # Padrão: **termo**: definição
        for match in re.finditer(r'\*\*([^*]+)\*\*[:\s]+(.+?)(?=\n\*\*|\n##|\n\n|$)', glossary, re.DOTALL):
            term = match.group(1).strip()
            definition = match.group(2).strip()

            concepts.append({
                "type": "glossary",
                "term": term,
                "definition": definition
            })

    # Extrai regras de negócio
    rules_match = re.search(r'## Regras de Negócio.*?\n(.+?)(?:\n## |$)', content, re.DOTALL)
    if rules_match:
        rules = rules_match.group(1)

        # Padrão: - **RN-XXX**: descrição
        for match in re.finditer(r'[-*]\s*\*\*([^*]+)\*\*[:\s]+(.+?)(?=\n[-*]|\n##|\n\n|$)', rules, re.DOTALL):
            rule_id = match.group(1).strip()
            description = match.group(2).strip()

            concepts.append({
                "type": "rule",
                "id": rule_id,
                "description": description
            })

    # Extrai entidades
    entities_match = re.search(r'## Entidades.*?\n(.+?)(?:\n## |\Z)', content, re.DOTALL)
    if entities_match:
        entities = entities_match.group(1)

        # Format 1: **entity**: description
        for match in re.finditer(r'\*\*([^*]+)\*\*[:\s]+(.+?)(?=\n\*\*|\n##|\n\n|\Z)', entities, re.DOTALL):
            entity = match.group(1).strip()
            description = match.group(2).strip()

            concepts.append({
                "type": "entity",
                "name": entity,
                "description": description
            })

        # Format 2: ### Subsection with code blocks or text
        seen_entities = {c["name"] for c in concepts if c["type"] == "entity"}
        for match in re.finditer(r'### (.+?)\n(.+?)(?=\n### |\n## |\Z)', entities, re.DOTALL):
            name = match.group(1).strip()
            body = match.group(2).strip()

            if name in seen_entities or not body:
                continue

            # Extract code block content if present
            code_blocks = re.findall(r'```\n?(.*?)```', body, re.DOTALL)
            description = '\n'.join(cb.strip() for cb in code_blocks) if code_blocks else body

            concepts.append({
                "type": "entity",
                "name": name,
                "description": description
            })

    # Extrai restrições
    constraints_match = re.search(r'## Restri[çc][õo]es.*?\n(.+?)(?:\n## |\Z)', content, re.DOTALL)
    if constraints_match:
        constraints = constraints_match.group(1)

        # Format 1: ### Subsections (e.g. ### Técnicas, ### De Design)
        has_subsections = bool(re.search(r'### ', constraints))
        if has_subsections:
            for match in re.finditer(r'### (.+?)\n(.+?)(?=\n### |\n## |\Z)', constraints, re.DOTALL):
                cat_name = match.group(1).strip()
                cat_content = match.group(2).strip()

                concepts.append({
                    "type": "constraint",
                    "name": f"Restrição: {cat_name}",
                    "description": cat_content
                })
        else:
            # Format 2: Flat bullet list
            for match in re.finditer(r'[-*]\s+(.+?)(?=\n[-*]|\n##|\n\n|\Z)', constraints, re.DOTALL):
                item = match.group(1).strip()
                concepts.append({
                    "type": "constraint",
                    "name": "Restrição",
                    "description": item
                })

    return concepts


def parse_patterns(content: str) -> List[Dict]:
    """Extrai patterns do PATTERNS.md.

    Handles multiple ## sections (Padrões Aprovados, Padrões de DevOps, etc.)
    and both English/Portuguese anti-pattern headers.
    """
    patterns = []

    # Remove code blocks and HTML comments to avoid false matches
    clean = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
    clean = re.sub(r'<!--.*?-->', '', clean, flags=re.DOTALL)

    # Split by ## headers and track section context
    for section_match in re.finditer(
        r'^(## .+?)$(.+?)(?=^## |\Z)', clean, re.MULTILINE | re.DOTALL
    ):
        section_header = section_match.group(1).strip()
        section_body = section_match.group(2)

        is_anti = bool(re.match(r'## Anti-', section_header))

        # Find all ### entries in this section
        for match in re.finditer(r'### (.+?)\n(.+?)(?=\n### |\n## |\Z)', section_body, re.DOTALL):
            name = match.group(1).strip()
            description = match.group(2).strip()

            # Skip templates (NNN placeholders)
            if 'NNN' in name:
                continue

            # Classify: anti-pattern section or ANTI-NNN prefix
            if is_anti or re.match(r'ANTI-\d+', name):
                ptype = "anti"
            else:
                ptype = "approved"

            patterns.append({
                "type": ptype,
                "name": name,
                "description": description
            })

    return patterns


def parse_git_commits(max_commits: int = 7000) -> List[Dict]:
    """Extrai informações dos commits do git"""
    commits = []

    try:
        # Formato: hash|author|date|subject|body
        result = subprocess.run(
            [
                "git", "log",
                f"-{max_commits}",
                "--pretty=format:%H|%an|%ae|%ai|%s|%b",
                "--no-merges"
            ],
            capture_output=True,
            text=True,
            cwd=Path(".").resolve()
        )

        if result.returncode != 0:
            print(f"Error running git log: {result.stderr}")
            return []

        lines = result.stdout.strip().split('\n')

        for line in lines:
            if not line.strip():
                continue

            parts = line.split('|', 5)
            if len(parts) < 5:
                continue

            commit_hash = parts[0][:8]  # Short hash
            author_name = parts[1]
            author_email = parts[2]
            date = parts[3].split()[0]  # Só a data, sem hora
            subject = parts[4]
            body = parts[5] if len(parts) > 5 else ""

            # Extrai tipo do commit (conventional commits)
            commit_type = "other"
            type_match = re.match(r'^(feat|fix|docs|style|refactor|test|chore|perf|ci|build|revert)[\(:]', subject.lower())
            if type_match:
                commit_type = type_match.group(1)

            # Extrai scope
            scope = None
            scope_match = re.match(r'^[a-z]+\(([^)]+)\)', subject.lower())
            if scope_match:
                scope = scope_match.group(1)

            # Extrai files modificados (se possível)
            files = []
            try:
                files_result = subprocess.run(
                    ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", parts[0]],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if files_result.returncode == 0:
                    files = [f for f in files_result.stdout.strip().split('\n') if f][:10]  # Max 10 files
            except:
                pass

            commits.append({
                "hash": commit_hash,
                "author_name": author_name,
                "author_email": author_email,
                "date": date,
                "subject": subject,
                "body": body,
                "type": commit_type,
                "scope": scope,
                "files": files
            })

    except Exception as e:
        print(f"Error parsing commits: {e}")

    return commits


def _extract_references(content: str) -> List[str]:
    """Extract cross-references from content.

    Finds: ADR-XXX, PAT-XXX, EXP-XXX, [[wikilinks]]
    Returns list of reference strings for brain.add_memory(references=...)
    """
    refs = []

    # ADR-NNN
    for m in re.finditer(r'\bADR-(\d+)\b', content, re.IGNORECASE):
        refs.append(f"ADR-{m.group(1).zfill(3)}")

    # PAT-NNN
    for m in re.finditer(r'\bPAT-(\d+)\b', content, re.IGNORECASE):
        refs.append(f"PAT-{m.group(1).zfill(3)}")

    # EXP-NNN
    for m in re.finditer(r'\bEXP-(\d+)\b', content, re.IGNORECASE):
        refs.append(f"EXP-{m.group(1).zfill(3)}")

    # [[wikilinks]]
    for m in re.finditer(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', content):
        refs.append(m.group(1).strip())

    return list(set(refs))  # deduplicate


def cross_reference_pass(brain: Brain) -> int:
    """Second pass: resolve references now that all nodes exist.

    Iterates all nodes, extracts refs from their content/summary,
    and creates REFERENCES edges where possible.
    """
    count = 0
    all_nodes = brain.get_all_nodes()

    for node_id, node_data in all_nodes.items():
        props = node_data.get("props", {})
        content = props.get("summary", "") + " " + props.get("title", "")

        refs = _extract_references(content)
        for ref in refs:
            target = brain._resolve_link(ref)
            if target and target != node_id and not brain.has_edge(node_id, target):
                brain.add_edge(node_id, target, "REFERENCES")
                count += 1

    return count


def migrate_content_to_graph(brain: Brain) -> int:
    """[ONE-TIME] Migrate content from disk (.md files) into graph props.content.

    For each node with content_path, reads the .md from disk, extracts
    content after the '---' separator, stores it in props.content,
    and removes content_path.

    Run: python3 populate.py migrate
    """
    all_nodes = brain.get_all_nodes()
    migrated = 0

    for nid, ndata in all_nodes.items():
        props = ndata.get("props", {})

        # Skip nodes that already have content
        if props.get("content"):
            continue

        # Try to read from content_path
        content_path = props.get("content_path")
        if content_path:
            full_path = brain.base_path.parent / content_path
            if full_path.exists():
                try:
                    raw = full_path.read_text(encoding="utf-8")
                    # Extract content after --- separator
                    parts = raw.split("---", 1)
                    content = parts[1].strip() if len(parts) > 1 else raw.strip()
                    props["content"] = content
                    # Update summary to 500 chars
                    props["summary"] = brain._generate_summary(content)
                    del props["content_path"]
                    ndata["props"] = props
                    migrated += 1
                except Exception as e:
                    print(f"  Error migrating {nid}: {e}")
                    continue
            else:
                # File doesn't exist, try to use summary as content
                summary = props.get("summary", "")
                if summary:
                    props["content"] = summary
                if "content_path" in props:
                    del props["content_path"]
                ndata["props"] = props
                migrated += 1
        else:
            # No content_path — use summary as content if available
            summary = props.get("summary", "")
            if summary and not props.get("content"):
                props["content"] = summary
                ndata["props"] = props
                migrated += 1

    return migrated


def populate_adrs(brain: Brain) -> int:
    """[MIGRATION ONLY] Adiciona ADRs ao cérebro"""
    adr_file = Path(".claude/knowledge/decisions/ADR_LOG.md")

    if not adr_file.exists():
        print(f"ADR file not found: {adr_file}")
        return 0

    content = adr_file.read_text(encoding='utf-8')
    adrs = parse_adr_log(content)

    count = 0
    for adr in adrs:
        # Pula template
        if "NNN" in adr["id"]:
            continue

        full_content = f"""## Contexto
{adr['context']}

## Decisão
{adr['decision']}

## Consequências
{adr['consequences']}
"""
        refs = _extract_references(adr.get("full_content", "") + full_content)

        node_id = brain.add_memory(
            title=f"{adr['id']}: {adr['title']}",
            content=full_content,
            labels=["Decision", "ADR"],
            author="@engram",
            props={
                "adr_id": adr["id"],
                "status": adr["status"],
                "date": adr["date"]
            },
            references=refs
        )
        count += 1
        print(f"  Added ADR: {adr['id']} -> {node_id}")

    return count


def populate_domain(brain: Brain) -> int:
    """[MIGRATION ONLY] Adiciona conceitos de domínio ao cérebro"""
    domain_file = Path(".claude/knowledge/domain/DOMAIN.md")

    if not domain_file.exists():
        print(f"Domain file not found: {domain_file}")
        return 0

    content = domain_file.read_text(encoding='utf-8')
    concepts = parse_domain(content)

    count = 0
    for concept in concepts:
        if concept["type"] == "glossary":
            node_id = brain.add_memory(
                title=concept["term"],
                content=concept["definition"],
                labels=["Concept", "Glossary"],
                author="@engram"
            )
            print(f"  Added concept: {concept['term']} -> {node_id}")

        elif concept["type"] == "rule":
            node_id = brain.add_memory(
                title=concept["id"],
                content=concept["description"],
                labels=["Concept", "Rule", "BusinessRule"],
                author="@engram",
                props={"rule_id": concept["id"]}
            )
            print(f"  Added rule: {concept['id']} -> {node_id}")

        elif concept["type"] == "entity":
            node_id = brain.add_memory(
                title=concept["name"],
                content=concept["description"],
                labels=["Concept", "Entity"],
                author="@engram"
            )
            print(f"  Added entity: {concept['name']} -> {node_id}")

        elif concept["type"] == "constraint":
            node_id = brain.add_memory(
                title=concept["name"],
                content=concept["description"],
                labels=["Concept", "Constraint"],
                author="@engram"
            )
            print(f"  Added constraint: {concept['name']} -> {node_id}")

        count += 1

    return count


def populate_patterns(brain: Brain) -> int:
    """[MIGRATION ONLY] Adiciona patterns ao cérebro"""
    patterns_file = Path(".claude/knowledge/patterns/PATTERNS.md")

    if not patterns_file.exists():
        print(f"Patterns file not found: {patterns_file}")
        return 0

    content = patterns_file.read_text(encoding='utf-8')
    patterns = parse_patterns(content)

    count = 0
    for pattern in patterns:
        labels = ["Pattern"]
        if pattern["type"] == "anti":
            labels.append("AntiPattern")
        else:
            labels.append("ApprovedPattern")

        refs = _extract_references(pattern["description"])
        # Extract pat_id from title (e.g. "PAT-001: Feedback Loop" -> "PAT-001")
        pat_props = {}
        pat_match = re.match(r'(PAT-\d+)', pattern["name"])
        if pat_match:
            pat_props["pat_id"] = pat_match.group(1)

        node_id = brain.add_memory(
            title=pattern["name"],
            content=pattern["description"],
            labels=labels,
            author="@engram",
            props=pat_props,
            references=refs
        )
        print(f"  Added pattern: {pattern['name']} -> {node_id}")
        count += 1

    return count


def populate_commits(brain: Brain, max_commits: int = 7000) -> int:
    """Adiciona commits ao cérebro como memória episódica"""
    print(f"Parsing up to {max_commits} commits...")
    commits = parse_git_commits(max_commits)
    print(f"Found {len(commits)} commits")

    count = 0
    batch_size = 100

    for i, commit in enumerate(commits):
        # Agrupa commits similares (mesmo autor, mesma data, mesmo tipo)
        # Para não criar milhares de nós individuais

        # Cria labels baseado no tipo
        labels = ["Episode", "Commit"]

        commit_type = commit["type"]
        if commit_type == "feat":
            labels.append("Feature")
        elif commit_type == "fix":
            labels.append("BugFix")
        elif commit_type == "refactor":
            labels.append("Refactor")
        elif commit_type == "docs":
            labels.append("Documentation")
        elif commit_type == "test":
            labels.append("Testing")
        elif commit_type == "perf":
            labels.append("Performance")

        # Adiciona scope como label se existir
        if commit["scope"]:
            scope_label = commit["scope"].replace("-", "").replace("_", "").title()
            if scope_label and len(scope_label) < 30:
                labels.append(f"{scope_label}Domain")

        # Prepara conteúdo
        content = f"""{commit['subject']}

{commit['body'] if commit['body'] else ''}

**Files changed:** {', '.join(commit['files'][:5]) if commit['files'] else 'N/A'}
""".strip()

        # Usa email como ID canônico do autor (ADR-010)
        author = commit["author_email"]

        refs = _extract_references(content)
        node_id = brain.add_memory(
            title=commit['subject'][:100],
            content=content,
            labels=labels,
            author=author,
            props={
                "commit_hash": commit["hash"],
                "date": commit["date"],
                "commit_type": commit_type,
                "scope": commit["scope"],
                "files_count": len(commit["files"]),
                "files": commit["files"][:5]
            },
            references=refs
        )
        count += 1

        if count % batch_size == 0:
            print(f"  Processed {count} commits...")

    return count


def populate_diffs(
    brain: Brain,
    max_commits: int = 20,
    since: str = None,
    unenriched_only: bool = False
) -> int:
    """Enrich existing Commit nodes with diff analysis.

    Parses unified diffs for recent commits, classifies symbols and change shapes,
    and appends structured summaries to Commit node content.

    Args:
        brain: Brain instance.
        max_commits: Maximum number of commits to process.
        since: Date filter (ISO format, e.g. "2025-01-01").
        unenriched_only: If True, only process commits without diff_enriched_at.

    Returns:
        Number of commits enriched.
    """
    from diff_parser import get_commits_with_diffs, analyze_diff

    print(f"Getting commits with diffs (max {max_commits})...")
    commits = get_commits_with_diffs(max_commits=max_commits, since=since)
    print(f"Found {len(commits)} commits with diffs")

    enriched = 0
    conn = brain._get_conn()

    for commit_hash, subject, diff_text in commits:
        short_hash = commit_hash[:8]

        # Find matching Commit node by commit_hash prop
        row = conn.execute(
            "SELECT id, properties FROM nodes WHERE json_extract(properties, '$.commit_hash') = ?",
            (short_hash,)
        ).fetchone()

        if not row:
            continue

        node_id = row["id"]
        props = json.loads(row["properties"])

        # Skip already enriched
        if unenriched_only and props.get("diff_enriched_at"):
            continue

        # Analyze diff
        try:
            result = analyze_diff(diff_text)
        except Exception as e:
            print(f"  Error analyzing diff for {short_hash}: {e}")
            continue

        # Build enrichment data
        diff_summary = result.summary_text
        diff_stats = result.diff_stats
        symbols_added = [f"{s.kind}:{s.name}" for s in result.symbols_added]
        symbols_modified = [f"{s.kind}:{s.name}" for s in result.symbols_modified]
        symbols_deleted = [f"{s.kind}:{s.name}" for s in result.symbols_deleted]
        change_shape = result.change_shape

        # Append to content
        content_append = f"\n--- Diff Summary ---\nShape: {change_shape} ({diff_stats['files_changed']} files, +{diff_stats['insertions']} -{diff_stats['deletions']})"
        if symbols_added:
            content_append += f"\nAdded: {', '.join(symbols_added[:10])}"
        if symbols_modified:
            content_append += f"\nModified: {', '.join(symbols_modified[:10])}"
        if symbols_deleted:
            content_append += f"\nDeleted: {', '.join(symbols_deleted[:10])}"

        # Update node
        extra_props = {
            "diff_summary": diff_summary,
            "diff_stats": json.dumps(diff_stats),
            "symbols_added": json.dumps(symbols_added),
            "symbols_modified": json.dumps(symbols_modified),
            "symbols_deleted": json.dumps(symbols_deleted),
            "change_shape": change_shape,
            "diff_enriched_at": datetime.now().isoformat(),
        }

        brain.update_node_content(
            node_id=node_id,
            content_append=content_append,
            extra_props=extra_props,
            regenerate_embedding=True
        )

        enriched += 1
        if enriched % 50 == 0:
            print(f"  Enriched {enriched} commits...")

    return enriched


def populate_experiences(brain: Brain) -> int:
    """[MIGRATION ONLY] Adiciona experiências ao cérebro como memória episódica."""
    exp_file = Path(".claude/knowledge/experiences/EXPERIENCE_LIBRARY.md")

    if not exp_file.exists():
        print(f"Experience file not found: {exp_file}")
        return 0

    content = exp_file.read_text(encoding='utf-8')

    count = 0
    sections = re.split(r'\n---\n', content)

    for section in sections:
        match = re.search(r'## (EXP-\d+): (.+)', section)
        if not match:
            continue

        exp_id = match.group(1)
        title = match.group(2).strip()

        # Extract fields
        context = ""
        ctx_match = re.search(r'\*\*Contexto\*\*: (.+?)(?=\n\*\*|\n---|\n## |$)', section, re.DOTALL)
        if ctx_match:
            context = ctx_match.group(1).strip()

        approach = ""
        app_match = re.search(r'\*\*Abordagem\*\*:\s*\n(.+?)(?=\n\*\*|\n---|\n## |$)', section, re.DOTALL)
        if app_match:
            approach = app_match.group(1).strip()

        exp_content = f"{context}\n{approach}".strip()
        refs = _extract_references(section)

        node_id = brain.add_memory(
            title=f"{exp_id}: {title}",
            content=exp_content,
            labels=["Episode", "Experience"],
            author="@engram",
            props={"exp_id": exp_id},
            references=refs
        )
        print(f"  Added experience: {exp_id} -> {node_id}")
        count += 1

    return count


def populate_ast(
    brain: Brain,
    root_dir: str = ".",
    languages: Optional[set] = None,
    dry_run: bool = False
) -> int:
    """Ingest code structure via AST parsing into the brain.

    Creates Code nodes (Module, Class, Function, Interface) and edges
    (DEFINES, IMPORTS, INHERITS, IMPLEMENTS, MEMBER_OF).

    Args:
        brain: Brain instance.
        root_dir: Root directory to scan.
        languages: Optional set of languages to filter.
        dry_run: If True, preview without writing to brain.

    Returns:
        Number of Code nodes created/updated.
    """
    from ast_parser import (
        scan_directory, generate_node_id, generate_content_text,
        ParseResult, ModuleInfo, ClassInfo, FunctionInfo, InterfaceInfo
    )

    # Get existing Module hashes for skip-on-rerun
    existing_hashes = {}
    conn = brain._get_conn()
    rows = conn.execute(
        """SELECT n.id, json_extract(n.properties, '$.file_path') AS fp,
                  json_extract(n.properties, '$.body_hash') AS bh
           FROM nodes n
           JOIN node_labels nl ON n.id = nl.node_id
           WHERE nl.label = 'Module'"""
    ).fetchall()
    for row in rows:
        if row["fp"] and row["bh"]:
            existing_hashes[row["fp"]] = row["bh"]

    print(f"Scanning {root_dir}" + (f" (languages: {languages})" if languages else ""))
    print(f"Existing modules with hashes: {len(existing_hashes)}")

    results = scan_directory(root_dir, languages=languages, existing_hashes=existing_hashes)
    print(f"Found {len(results)} files to process")

    if dry_run:
        for r in results:
            print(f"  {r.module.file_path}: {r.module.symbol_count} symbols")
        return 0

    created = 0

    for result in results:
        mod = result.module
        mod_id = generate_node_id(mod.file_path, mod.file_path, "Module")

        # Module node
        mod_content = generate_content_text(mod)
        brain.add_memory(
            title=f"Module: {Path(mod.file_path).stem}",
            content=mod_content,
            labels=["Code", "Module"],
            author="@ast-parser",
            props={
                "file_path": mod.file_path,
                "language": mod.language,
                "line_count": mod.line_count,
                "import_count": mod.import_count,
                "symbol_count": mod.symbol_count,
                "body_hash": mod.body_hash,
            },
            node_id=mod_id,
        )
        created += 1

        # Class nodes
        for cls in result.classes:
            cls_id = generate_node_id(cls.file_path, cls.qualified_name, "Class")
            cls_content = generate_content_text(cls)
            brain.add_memory(
                title=f"Class: {cls.qualified_name}",
                content=cls_content,
                labels=["Code", "Class"],
                author="@ast-parser",
                props={
                    "file_path": cls.file_path,
                    "language": cls.language,
                    "name": cls.name,
                    "qualified_name": cls.qualified_name,
                    "line_start": cls.line_start,
                    "line_end": cls.line_end,
                    "docstring": cls.docstring,
                    "base_classes": json.dumps(cls.base_classes),
                    "detected_pattern": cls.detected_pattern,
                },
                node_id=cls_id,
            )
            created += 1

            # DEFINES edge: Module -> Class
            brain.add_edge(mod_id, cls_id, "DEFINES", 0.8)

            # INHERITS edges
            for base in cls.base_classes:
                # Try to find base class node
                base_row = conn.execute(
                    "SELECT id FROM nodes WHERE json_extract(properties, '$.name') = ? "
                    "AND id IN (SELECT node_id FROM node_labels WHERE label = 'Class')",
                    (base,)
                ).fetchone()
                if base_row:
                    brain.add_edge(cls_id, base_row["id"], "INHERITS", 0.7)

        # Function nodes
        for fn in result.functions:
            fn_id = generate_node_id(fn.file_path, fn.qualified_name, "Function")
            fn_content = generate_content_text(fn)
            brain.add_memory(
                title=f"Function: {fn.qualified_name}",
                content=fn_content,
                labels=["Code", "Function"],
                author="@ast-parser",
                props={
                    "file_path": fn.file_path,
                    "language": fn.language,
                    "name": fn.name,
                    "qualified_name": fn.qualified_name,
                    "signature": fn.signature,
                    "line_start": fn.line_start,
                    "line_end": fn.line_end,
                    "docstring": fn.docstring,
                    "is_method": fn.is_method,
                    "param_count": fn.param_count,
                    "complexity_hint": fn.complexity_hint,
                },
                node_id=fn_id,
            )
            created += 1

            if fn.is_method:
                # MEMBER_OF edge: Function -> Class
                # Find parent class by qualified_name prefix
                parts = fn.qualified_name.rsplit('.', 1)
                if len(parts) == 2:
                    class_qn = parts[0]
                    cls_row = conn.execute(
                        "SELECT id FROM nodes WHERE json_extract(properties, '$.qualified_name') = ? "
                        "AND id IN (SELECT node_id FROM node_labels WHERE label = 'Class')",
                        (class_qn,)
                    ).fetchone()
                    if cls_row:
                        brain.add_edge(fn_id, cls_row["id"], "MEMBER_OF", 0.8)
            else:
                # DEFINES edge: Module -> Function
                brain.add_edge(mod_id, fn_id, "DEFINES", 0.8)

        # Interface nodes
        for iface in result.interfaces:
            iface_id = generate_node_id(iface.file_path, iface.qualified_name, "Interface")
            iface_content = generate_content_text(iface)
            brain.add_memory(
                title=f"Interface: {iface.qualified_name}",
                content=iface_content,
                labels=["Code", "Interface"],
                author="@ast-parser",
                props={
                    "file_path": iface.file_path,
                    "language": iface.language,
                    "name": iface.name,
                    "qualified_name": iface.qualified_name,
                    "line_start": iface.line_start,
                    "line_end": iface.line_end,
                    "method_signatures": json.dumps(iface.method_signatures),
                },
                node_id=iface_id,
            )
            created += 1

            # DEFINES edge: Module -> Interface
            brain.add_edge(mod_id, iface_id, "DEFINES", 0.8)

        # IMPORTS edges: Module -> Module (by import name)
        for imp in mod.imports:
            # Try to find imported module
            imp_row = conn.execute(
                """SELECT n.id FROM nodes n
                   JOIN node_labels nl ON n.id = nl.node_id
                   WHERE nl.label = 'Module'
                   AND (json_extract(n.properties, '$.file_path') LIKE ? OR n.title LIKE ?)""",
                (f"%{imp}%", f"Module: {imp}")
            ).fetchone()
            if imp_row and imp_row["id"] != mod_id:
                brain.add_edge(mod_id, imp_row["id"], "IMPORTS", 0.5)

        if created % 100 == 0 and created > 0:
            print(f"  Created {created} Code nodes...")

    return created


def main():
    if len(sys.argv) < 2:
        print("Usage: populate.py <command> [args]")
        print("Commands:")
        print("  migrate          [ONE-TIME] Migrate content from disk to in-graph")
        print("  refresh          Shortcut: commits + diffs + cross-refs")
        print("  all              Process everything (migration only)")
        print("  adrs             Process ADRs only (migration only)")
        print("  domain           Process domain concepts only (migration only)")
        print("  patterns         Process patterns only (migration only)")
        print("  experiences      Process experiences only (migration only)")
        print("  commits [N]      Process last N commits (default: 7000)")
        print("  diffs            Enrich commits with diff analysis")
        print("  ast [dir]        Ingest code structure via AST parsing")
        print("  stats            Show current brain stats")
        sys.exit(1)

    cmd = sys.argv[1]

    brain = Brain()
    brain.load()

    if cmd == "stats":
        stats = brain.get_stats()
        print(json.dumps(stats, indent=2))
        return

    if cmd == "migrate":
        print("\n=== Migrating Content to In-Graph ===")
        count = migrate_content_to_graph(brain)
        print(f"Migrated {count} nodes")
        # Verify
        all_nodes = brain.get_all_nodes()
        with_content = sum(1 for n in all_nodes.values() if n.get("props", {}).get("content"))
        print(f"Nodes with props.content: {with_content}")
        brain.save()
        print(json.dumps(brain.get_stats(), indent=2))
        return

    if cmd == "refresh":
        # Shortcut: commits + diff enrichment + AST incremental + cross-refs
        max_commits = 20
        if len(sys.argv) > 2:
            try:
                max_commits = int(sys.argv[2])
            except:
                pass

        print(f"\n=== Refresh: Commits (max {max_commits}) + Diffs + AST + Cross-Refs ===")
        count = populate_commits(brain, max_commits)
        print(f"Added {count} commits")

        # Enrich new commits with diffs
        print(f"\n=== Diff Enrichment ===")
        try:
            diff_count = populate_diffs(brain, max_commits=max_commits, unenriched_only=True)
            print(f"Enriched {diff_count} commits with diff analysis")
        except Exception as e:
            print(f"Diff enrichment skipped: {e}")

        # Incremental AST — only if already initialized (Code nodes exist)
        conn = brain._get_conn()
        code_count = conn.execute(
            "SELECT COUNT(*) AS cnt FROM node_labels WHERE label = 'Module'"
        ).fetchone()["cnt"]
        if code_count > 0:
            print(f"\n=== AST Incremental ({code_count} modules tracked) ===")
            try:
                ast_count = populate_ast(brain, root_dir=".")
                print(f"Updated {ast_count} Code nodes")
            except Exception as e:
                print(f"AST incremental skipped: {e}")
        else:
            print(f"\n=== AST Skipped (no Code nodes yet — run 'populate.py ast' first) ===")

        if count > 0:
            print(f"\n=== Cross-Reference Pass ===")
            xref_count = cross_reference_pass(brain)
            print(f"Created {xref_count} cross-reference edges")

        brain.save()
        print(json.dumps(brain.get_stats(), indent=2))
        return

    if cmd == "diffs":
        # Parse CLI args for diffs
        max_commits = 20
        since = None
        unenriched = False

        i = 2
        while i < len(sys.argv):
            arg = sys.argv[i]
            if arg == "--since" and i + 1 < len(sys.argv):
                since = sys.argv[i + 1]
                i += 2
            elif arg == "--max" and i + 1 < len(sys.argv):
                try:
                    max_commits = int(sys.argv[i + 1])
                except ValueError:
                    pass
                i += 2
            elif arg == "--unenriched":
                unenriched = True
                i += 1
            else:
                try:
                    max_commits = int(arg)
                except ValueError:
                    pass
                i += 1

        print(f"\n=== Diff Enrichment (max {max_commits}" +
              (f", since {since}" if since else "") +
              (", unenriched only" if unenriched else "") + ") ===")
        count = populate_diffs(brain, max_commits=max_commits, since=since, unenriched_only=unenriched)
        print(f"Enriched {count} commits")
        brain.save()
        print(json.dumps(brain.get_stats(), indent=2))
        return

    if cmd == "ast":
        # Parse CLI args for ast
        root_dir = "."
        languages = None
        dry_run = "--dry-run" in sys.argv

        args = [a for a in sys.argv[2:] if not a.startswith('--')]
        if args:
            root_dir = args[0]

        for i, a in enumerate(sys.argv):
            if a == '--lang' and i + 1 < len(sys.argv):
                lang_filter = sys.argv[i + 1].split(',')
                short_map = {'py': 'python', 'js': 'javascript', 'ts': 'typescript', 'rb': 'ruby'}
                languages = {short_map.get(l, l) for l in lang_filter}

        print(f"\n=== AST Ingestion ({root_dir})" +
              (f" [languages: {languages}]" if languages else "") +
              (" [DRY RUN]" if dry_run else "") + " ===")
        count = populate_ast(brain, root_dir=root_dir, languages=languages, dry_run=dry_run)
        print(f"Created {count} Code nodes")
        if not dry_run:
            brain.save()
            print(json.dumps(brain.get_stats(), indent=2))
        return

    total = 0

    if cmd in ["all", "adrs"]:
        print("\n=== Processing ADRs ===")
        count = populate_adrs(brain)
        print(f"Added {count} ADRs")
        total += count

    if cmd in ["all", "domain"]:
        print("\n=== Processing Domain ===")
        count = populate_domain(brain)
        print(f"Added {count} domain concepts")
        total += count

    if cmd in ["all", "patterns"]:
        print("\n=== Processing Patterns ===")
        count = populate_patterns(brain)
        print(f"Added {count} patterns")
        total += count

    if cmd in ["all", "experiences"]:
        print("\n=== Processing Experiences ===")
        count = populate_experiences(brain)
        print(f"Added {count} experiences")
        total += count

    if cmd in ["all", "commits"]:
        max_commits = 7000
        if len(sys.argv) > 2:
            try:
                max_commits = int(sys.argv[2])
            except:
                pass

        print(f"\n=== Processing Commits (max {max_commits}) ===")
        count = populate_commits(brain, max_commits)
        print(f"Added {count} commits")
        total += count

    if cmd == "all":
        # AST ingestion — mandatory in full population (used by /init-engram)
        print(f"\n=== Processing AST (full codebase) ===")
        try:
            ast_count = populate_ast(brain, root_dir=".")
            print(f"Created {ast_count} Code nodes")
            total += ast_count
        except Exception as e:
            print(f"AST ingestion failed: {e}")

        # Enrich commits with diff analysis
        print(f"\n=== Diff Enrichment ===")
        try:
            diff_count = populate_diffs(brain, max_commits=200, unenriched_only=True)
            print(f"Enriched {diff_count} commits with diff analysis")
        except Exception as e:
            print(f"Diff enrichment skipped: {e}")

    if total > 0:
        # Second pass: cross-reference now that all nodes exist
        print(f"\n=== Cross-Reference Pass ===")
        xref_count = cross_reference_pass(brain)
        print(f"Created {xref_count} cross-reference edges")

        print(f"\n=== Saving Brain ===")
        brain.save()

        print(f"\n=== Final Stats ===")
        stats = brain.get_stats()
        print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
