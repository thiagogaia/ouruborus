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
from brain import Brain, get_current_developer


def parse_adr_log(content: str) -> List[Dict]:
    """Extrai ADRs do ADR_LOG.md"""
    adrs = []

    # Pattern para encontrar ADRs
    adr_pattern = re.compile(
        r'## (ADR-\d+): (.+?)\n'
        r'\*\*Data\*\*: (.+?)\n'
        r'\*\*Status\*\*: (.+?)\n'
        r'(?:\*\*(?:Decisores|Relacionado)\*\*: (.+?)\n)?'
        r'.*?### Contexto\n(.+?)\n###',
        re.DOTALL
    )

    # Pattern alternativo mais simples
    simple_pattern = re.compile(
        r'## (ADR-\d+): (.+?)\n',
        re.MULTILINE
    )

    # Divide por ADRs
    sections = re.split(r'\n---\n', content)

    for section in sections:
        # Tenta extrair informações básicas
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

        # Extrai contexto
        context_match = re.search(r'### Contexto\n(.+?)(?:\n###|\n## |$)', section, re.DOTALL)
        context = context_match.group(1).strip() if context_match else ""

        # Extrai decisão
        decision_match = re.search(r'### Decisão\n(.+?)(?:\n###|\n## |$)', section, re.DOTALL)
        decision = decision_match.group(1).strip() if decision_match else ""

        # Extrai consequências
        conseq_match = re.search(r'### Consequências\n(.+?)(?:\n---|\n## |$)', section, re.DOTALL)
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
    entities_match = re.search(r'## Entidades.*?\n(.+?)(?:\n## |$)', content, re.DOTALL)
    if entities_match:
        entities = entities_match.group(1)

        for match in re.finditer(r'\*\*([^*]+)\*\*[:\s]+(.+?)(?=\n\*\*|\n##|\n\n|$)', entities, re.DOTALL):
            entity = match.group(1).strip()
            description = match.group(2).strip()

            concepts.append({
                "type": "entity",
                "name": entity,
                "description": description
            })

    return concepts


def parse_patterns(content: str) -> List[Dict]:
    """Extrai patterns do PATTERNS.md"""
    patterns = []

    # Extrai padrões aprovados
    approved_match = re.search(r'## Padrões Aprovados.*?\n(.+?)(?:\n## Anti|$)', content, re.DOTALL)
    if approved_match:
        approved = approved_match.group(1)

        # Padrão: ### Nome do Pattern
        for match in re.finditer(r'### (.+?)\n(.+?)(?=\n###|\n## |$)', approved, re.DOTALL):
            name = match.group(1).strip()
            description = match.group(2).strip()

            patterns.append({
                "type": "approved",
                "name": name,
                "description": description
            })

    # Extrai anti-patterns
    anti_match = re.search(r'## Anti-[Pp]atterns.*?\n(.+?)(?:\n## |$)', content, re.DOTALL)
    if anti_match:
        anti = anti_match.group(1)

        for match in re.finditer(r'### (.+?)\n(.+?)(?=\n###|\n## |$)', anti, re.DOTALL):
            name = match.group(1).strip()
            description = match.group(2).strip()

            patterns.append({
                "type": "anti",
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


def populate_adrs(brain: Brain) -> int:
    """Adiciona ADRs ao cérebro"""
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
    """Adiciona conceitos de domínio ao cérebro"""
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

        count += 1

    return count


def populate_patterns(brain: Brain) -> int:
    """Adiciona patterns ao cérebro"""
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

        # Extrai autor como @username
        author_email = commit["author_email"]
        author_username = re.sub(r'[^a-z0-9]', '-', author_email.split("@")[0].lower())
        author = f"@{author_username}"

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


def populate_experiences(brain: Brain) -> int:
    """Adiciona experiências ao cérebro como memória episódica."""
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


def main():
    if len(sys.argv) < 2:
        print("Usage: populate.py <command> [args]")
        print("Commands:")
        print("  all              Process everything")
        print("  adrs             Process ADRs only")
        print("  domain           Process domain concepts only")
        print("  patterns         Process patterns only")
        print("  experiences      Process experiences only")
        print("  commits [N]      Process last N commits (default: 7000)")
        print("  stats            Show current brain stats")
        sys.exit(1)

    cmd = sys.argv[1]

    brain = Brain()
    brain.load()

    if cmd == "stats":
        stats = brain.get_stats()
        print(json.dumps(stats, indent=2))
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
