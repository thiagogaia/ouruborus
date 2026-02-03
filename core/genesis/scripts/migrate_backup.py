#!/usr/bin/env python3
"""
Engram Genesis — Backup Migration Tool
Detects, analyzes, and merges content from backup files created by setup.sh.

Usage:
    python3 migrate_backup.py --project-dir . --detect
    python3 migrate_backup.py --project-dir . --analyze
    python3 migrate_backup.py --project-dir . --migrate --strategy smart
    python3 migrate_backup.py --project-dir . --cleanup
"""

import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


# ══════════════════════════════════════════════════════════════════════════════
# DETECTION
# ══════════════════════════════════════════════════════════════════════════════

def detect_backups(project_dir: str) -> dict:
    """
    Detect backup files/directories created by setup.sh.

    Returns dict with:
        - found: bool (any backup exists)
        - claude_dir_bak: path or None
        - claude_md_bak: path or None
        - manifest_bak: path or None (inside .claude.bak/)
        - settings_bak: path or None (inside .claude.bak/)
        - knowledge_bak: dict of knowledge files found
        - custom_skills: list of non-core skills
        - custom_commands: list of custom commands
    """
    p = Path(project_dir)
    result = {
        "found": False,
        "claude_dir_bak": None,
        "claude_md_bak": None,
        "manifest_bak": None,
        "settings_bak": None,
        "knowledge_bak": {},
        "custom_skills": [],
        "custom_commands": [],
        "custom_agents": [],
    }

    # Check .claude.bak/
    claude_bak = p / ".claude.bak"
    if claude_bak.is_dir():
        result["found"] = True
        result["claude_dir_bak"] = str(claude_bak)

        # Check manifest
        manifest_bak = claude_bak / "manifest.json"
        if manifest_bak.is_file():
            result["manifest_bak"] = str(manifest_bak)

        # Check settings
        settings_bak = claude_bak / "settings.json"
        if settings_bak.is_file():
            result["settings_bak"] = str(settings_bak)

        # Check knowledge files
        knowledge_dir = claude_bak / "knowledge"
        if knowledge_dir.is_dir():
            for subdir in ["context", "priorities", "patterns", "decisions", "domain", "experiences"]:
                subpath = knowledge_dir / subdir
                if subpath.is_dir():
                    for f in subpath.glob("*.md"):
                        key = f"{subdir}/{f.name}"
                        result["knowledge_bak"][key] = str(f)

        # Check for custom skills (non-core)
        core_skills = {
            "engram-genesis", "engram-evolution", "project-analyzer",
            "knowledge-manager", "domain-expert", "priority-engine",
            "code-reviewer", "engram-factory"
        }
        skills_dir = claude_bak / "skills"
        if skills_dir.is_dir():
            for skill in skills_dir.iterdir():
                if skill.is_dir() and skill.name not in core_skills:
                    result["custom_skills"].append(skill.name)

        # Check for custom commands
        core_commands = {
            "commit", "create", "curriculum", "doctor", "export", "import",
            "init-engram", "learn", "plan", "priorities", "review", "spawn", "status"
        }
        commands_dir = claude_bak / "commands"
        if commands_dir.is_dir():
            for cmd in commands_dir.glob("*.md"):
                name = cmd.stem
                if name not in core_commands:
                    result["custom_commands"].append(name)

        # Check for custom agents
        core_agents = {"architect", "domain-analyst", "db-expert"}
        agents_dir = claude_bak / "agents"
        if agents_dir.is_dir():
            for agent in agents_dir.glob("*.md"):
                name = agent.stem
                if name not in core_agents:
                    result["custom_agents"].append(name)

    # Check CLAUDE.md.bak
    claude_md_bak = p / "CLAUDE.md.bak"
    if claude_md_bak.is_file():
        result["found"] = True
        result["claude_md_bak"] = str(claude_md_bak)

    return result


# ══════════════════════════════════════════════════════════════════════════════
# ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════

def analyze_claude_md_bak(path: str) -> dict:
    """Extract valuable content from CLAUDE.md.bak."""
    content = Path(path).read_text()
    analysis = {
        "custom_rules": [],
        "custom_sections": [],
        "project_name": None,
        "stack_info": [],
    }

    # Extract project name
    name_match = re.search(r"^#\s*(?:Projeto:|Project:)?\s*(.+)$", content, re.MULTILINE)
    if name_match:
        analysis["project_name"] = name_match.group(1).strip()

    # Extract custom rules (lines starting with - in "Ao Codificar" or similar sections)
    rules_section = re.search(
        r"(?:Ao Codificar|Coding Rules|Rules).*?\n((?:[-*].*\n)+)",
        content, re.IGNORECASE | re.DOTALL
    )
    if rules_section:
        for line in rules_section.group(1).split("\n"):
            line = line.strip()
            if line.startswith(("-", "*")) and len(line) > 10:
                rule = line.lstrip("-* ").strip()
                # Skip generic rules that come from template
                if not any(generic in rule.lower() for generic in [
                    "validação de input", "error handling", "nunca any",
                    "server components"
                ]):
                    analysis["custom_rules"].append(rule)

    # Extract stack info
    stack_section = re.search(r"##\s*Stack\n((?:[-*].*\n)+)", content)
    if stack_section:
        for line in stack_section.group(1).split("\n"):
            line = line.strip()
            if line.startswith(("-", "*")):
                analysis["stack_info"].append(line.lstrip("-* ").strip())

    # Find custom sections (not standard Engram sections)
    standard_sections = {
        "identidade", "princípio central", "workflow obrigatório",
        "antes de codificar", "ao codificar", "depois de codificar",
        "stack", "auto-geração", "skills disponíveis", "subagentes",
        "orquestração inteligente", "regras de ouro"
    }
    for match in re.finditer(r"^##\s*(.+)$", content, re.MULTILINE):
        section_name = match.group(1).strip().lower()
        # Normalize
        section_name_normalized = re.sub(r"\s*\(.*\)", "", section_name)
        if section_name_normalized not in standard_sections:
            # Extract the section content
            start = match.end()
            next_section = re.search(r"^##\s", content[start:], re.MULTILINE)
            end = start + next_section.start() if next_section else len(content)
            section_content = content[start:end].strip()
            if len(section_content) > 20:  # Only meaningful sections
                analysis["custom_sections"].append({
                    "name": match.group(1).strip(),
                    "content": section_content[:500]  # Limit size
                })

    return analysis


def analyze_settings_bak(path: str) -> dict:
    """Extract custom permissions from settings.json.bak."""
    try:
        data = json.loads(Path(path).read_text())
    except (json.JSONDecodeError, FileNotFoundError):
        return {"allow": [], "deny": []}

    permissions = data.get("permissions", {})

    # Standard permissions from setup.sh template
    standard_allow = {
        "Read", "Write", "Edit", "Glob", "Grep",
        "Bash(git add:*)", "Bash(git status:*)", "Bash(git commit:*)",
        "Bash(git log:*)", "Bash(git diff:*)", "Bash(git branch:*)",
        "Bash(cat:*)", "Bash(ls:*)", "Bash(find:*)", "Bash(grep:*)",
        "Bash(head:*)", "Bash(tail:*)", "Bash(wc:*)", "Bash(mkdir:*)",
        "Bash(echo:*)", "Bash(python3:*)", "Bash(npx:*)",
        "Bash(docker compose:*)"
    }
    standard_deny = {
        "Bash(rm -rf /)*",
        "Read(.env)", "Read(.env.local)", "Read(.env.production)"
    }

    custom_allow = []
    custom_deny = []

    for perm in permissions.get("allow", []):
        # Check if it's a package manager specific or standard
        if perm not in standard_allow:
            # Ignore package manager variants
            if not any(pm in perm for pm in ["pnpm", "yarn", "bun", "npm run"]):
                custom_allow.append(perm)

    for perm in permissions.get("deny", []):
        if perm not in standard_deny:
            custom_deny.append(perm)

    return {
        "allow": custom_allow,
        "deny": custom_deny,
    }


def analyze_knowledge_file(path: str, filename: str) -> dict:
    """Analyze a knowledge file to determine if it has custom content."""
    content = Path(path).read_text()

    # Template markers indicating auto-generated/empty content
    template_markers = [
        "[TODO:", "[A definir]", "[Auto-detectado]", "[Vazio]",
        "Pendente análise", "rode /init-engram", "será populada pelo"
    ]

    # Check if it's mostly template content
    is_template = any(marker in content for marker in template_markers)

    # Count meaningful lines (not headers, not empty, not template)
    lines = content.split("\n")
    meaningful_lines = 0
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("#"):
            continue
        if line.startswith(">"):
            continue
        if any(marker in line for marker in template_markers):
            continue
        if len(line) > 20:
            meaningful_lines += 1

    return {
        "path": path,
        "filename": filename,
        "is_template": is_template,
        "meaningful_lines": meaningful_lines,
        "has_custom_content": meaningful_lines > 5 and not is_template,
        "size_bytes": len(content),
    }


def full_analysis(project_dir: str) -> dict:
    """Complete analysis of all backups."""
    backups = detect_backups(project_dir)

    if not backups["found"]:
        return {"found": False, "backups": backups}

    analysis = {
        "found": True,
        "backups": backups,
        "claude_md_analysis": None,
        "settings_analysis": None,
        "knowledge_analysis": {},
        "migration_recommendations": [],
    }

    # Analyze CLAUDE.md.bak
    if backups["claude_md_bak"]:
        analysis["claude_md_analysis"] = analyze_claude_md_bak(backups["claude_md_bak"])
        if analysis["claude_md_analysis"]["custom_rules"]:
            analysis["migration_recommendations"].append({
                "type": "rules",
                "action": "merge",
                "description": f"Mesclar {len(analysis['claude_md_analysis']['custom_rules'])} regras customizadas no CLAUDE.md",
                "priority": "high"
            })
        if analysis["claude_md_analysis"]["custom_sections"]:
            analysis["migration_recommendations"].append({
                "type": "sections",
                "action": "merge",
                "description": f"Mesclar {len(analysis['claude_md_analysis']['custom_sections'])} seções customizadas",
                "priority": "medium"
            })

    # Analyze settings.json.bak
    if backups["settings_bak"]:
        analysis["settings_analysis"] = analyze_settings_bak(backups["settings_bak"])
        custom_perms = len(analysis["settings_analysis"]["allow"]) + len(analysis["settings_analysis"]["deny"])
        if custom_perms > 0:
            analysis["migration_recommendations"].append({
                "type": "permissions",
                "action": "merge",
                "description": f"Mesclar {custom_perms} permissões customizadas no settings.json",
                "priority": "high"
            })

    # Analyze knowledge files
    for key, path in backups["knowledge_bak"].items():
        ka = analyze_knowledge_file(path, key)
        analysis["knowledge_analysis"][key] = ka
        if ka["has_custom_content"]:
            analysis["migration_recommendations"].append({
                "type": "knowledge",
                "file": key,
                "action": "merge",
                "description": f"Mesclar conteúdo de {key} ({ka['meaningful_lines']} linhas úteis)",
                "priority": "high" if "EXPERIENCE" in key or "PATTERN" in key else "medium"
            })

    # Custom components
    if backups["custom_skills"]:
        analysis["migration_recommendations"].append({
            "type": "skills",
            "action": "preserve",
            "description": f"Preservar {len(backups['custom_skills'])} skills customizados: {', '.join(backups['custom_skills'])}",
            "priority": "high"
        })

    if backups["custom_commands"]:
        analysis["migration_recommendations"].append({
            "type": "commands",
            "action": "preserve",
            "description": f"Preservar {len(backups['custom_commands'])} commands customizados: {', '.join(backups['custom_commands'])}",
            "priority": "high"
        })

    if backups["custom_agents"]:
        analysis["migration_recommendations"].append({
            "type": "agents",
            "action": "preserve",
            "description": f"Preservar {len(backups['custom_agents'])} agents customizados: {', '.join(backups['custom_agents'])}",
            "priority": "high"
        })

    return analysis


# ══════════════════════════════════════════════════════════════════════════════
# MIGRATION
# ══════════════════════════════════════════════════════════════════════════════

def merge_settings(project_dir: str, settings_analysis: dict) -> bool:
    """Merge custom permissions into current settings.json."""
    settings_path = Path(project_dir) / ".claude" / "settings.json"

    if not settings_path.is_file():
        print("  ⚠️  settings.json não encontrado")
        return False

    try:
        current = json.loads(settings_path.read_text())
    except json.JSONDecodeError:
        print("  ⚠️  settings.json inválido")
        return False

    # Merge allow
    current_allow = set(current.get("permissions", {}).get("allow", []))
    for perm in settings_analysis["allow"]:
        if perm not in current_allow:
            current_allow.add(perm)
            print(f"    ✅ Adicionada permissão: {perm}")

    # Merge deny
    current_deny = set(current.get("permissions", {}).get("deny", []))
    for perm in settings_analysis["deny"]:
        if perm not in current_deny:
            current_deny.add(perm)
            print(f"    ✅ Adicionada restrição: {perm}")

    # Update and save
    if "permissions" not in current:
        current["permissions"] = {}
    current["permissions"]["allow"] = sorted(list(current_allow))
    current["permissions"]["deny"] = sorted(list(current_deny))

    settings_path.write_text(json.dumps(current, indent=2, ensure_ascii=False))
    return True


def merge_knowledge_file(src_path: str, dest_path: str) -> bool:
    """
    Smart merge of knowledge files.
    Strategy: Append unique entries from backup that aren't in the new file.
    """
    src = Path(src_path)
    dest = Path(dest_path)

    if not src.is_file():
        return False

    if not dest.is_file():
        # Just copy
        shutil.copy2(src, dest)
        return True

    src_content = src.read_text()
    dest_content = dest.read_text()

    # For EXPERIENCE_LIBRARY: append entries
    if "EXPERIENCE" in str(src_path):
        # Find entries (## headers with content)
        src_entries = re.findall(r"(##\s*EXP-\d+[^\n]*\n(?:(?!##).*\n)*)", src_content)
        existing_ids = set(re.findall(r"##\s*(EXP-\d+)", dest_content))

        new_entries = []
        for entry in src_entries:
            entry_id = re.search(r"##\s*(EXP-\d+)", entry)
            if entry_id and entry_id.group(1) not in existing_ids:
                new_entries.append(entry.strip())

        if new_entries:
            with open(dest, "a") as f:
                f.write("\n\n<!-- Migrado do backup -->\n")
                for entry in new_entries:
                    f.write(f"\n{entry}\n")
            print(f"    ✅ Mescladas {len(new_entries)} experiências")
        return True

    # For PATTERNS: append pattern entries
    if "PATTERN" in str(src_path):
        src_patterns = re.findall(r"(###\s*PAT-\d+[^\n]*\n(?:(?!###).*\n)*)", src_content)
        existing_ids = set(re.findall(r"###\s*(PAT-\d+)", dest_content))

        new_patterns = []
        for pattern in src_patterns:
            pattern_id = re.search(r"###\s*(PAT-\d+)", pattern)
            if pattern_id and pattern_id.group(1) not in existing_ids:
                new_patterns.append(pattern.strip())

        if new_patterns:
            with open(dest, "a") as f:
                f.write("\n\n<!-- Migrado do backup -->\n")
                for pattern in new_patterns:
                    f.write(f"\n{pattern}\n")
            print(f"    ✅ Mesclados {len(new_patterns)} padrões")
        return True

    # For ADR_LOG: append ADR entries
    if "ADR" in str(src_path):
        src_adrs = re.findall(r"(##\s*ADR-\d+[^\n]*\n(?:(?!##\s*ADR).*\n)*)", src_content)
        existing_ids = set(re.findall(r"##\s*(ADR-\d+)", dest_content))

        new_adrs = []
        for adr in src_adrs:
            adr_id = re.search(r"##\s*(ADR-\d+)", adr)
            if adr_id and adr_id.group(1) not in existing_ids:
                new_adrs.append(adr.strip())

        if new_adrs:
            with open(dest, "a") as f:
                f.write("\n\n<!-- Migrado do backup -->\n")
                for adr in new_adrs:
                    f.write(f"\n{adr}\n")
            print(f"    ✅ Mesclados {len(new_adrs)} ADRs")
        return True

    # For DOMAIN: append glossary entries
    if "DOMAIN" in str(src_path):
        # Extract glossary items (- **Term**: definition)
        src_terms = re.findall(r"(-\s*\*\*[^*]+\*\*:[^\n]+)", src_content)
        existing_terms = set(re.findall(r"-\s*\*\*([^*]+)\*\*:", dest_content))

        new_terms = []
        for term in src_terms:
            term_name = re.search(r"\*\*([^*]+)\*\*", term)
            if term_name and term_name.group(1) not in existing_terms:
                new_terms.append(term.strip())

        if new_terms:
            with open(dest, "a") as f:
                f.write("\n\n<!-- Migrado do backup -->\n")
                for term in new_terms:
                    f.write(f"\n{term}")
            print(f"    ✅ Mesclados {len(new_terms)} termos do domínio")
        return True

    # For PRIORITY_MATRIX: append priority items
    if "PRIORITY" in str(src_path):
        # Just note that manual review is needed for priorities
        print(f"    ⚠️  PRIORITY_MATRIX requer revisão manual (prioridades mudam)")
        return True

    # For CURRENT_STATE: the new one is always more accurate
    if "CURRENT_STATE" in str(src_path):
        print(f"    ℹ️  CURRENT_STATE usa versão nova (estado atual)")
        return True

    return False


def preserve_custom_components(project_dir: str, backups: dict) -> int:
    """Copy custom skills, commands, agents from backup."""
    count = 0
    p = Path(project_dir)
    bak = Path(backups["claude_dir_bak"]) if backups["claude_dir_bak"] else None

    if not bak:
        return 0

    # Preserve custom skills
    for skill_name in backups.get("custom_skills", []):
        src = bak / "skills" / skill_name
        dest = p / ".claude" / "skills" / skill_name
        if src.is_dir() and not dest.exists():
            shutil.copytree(src, dest)
            print(f"    ✅ Skill preservado: {skill_name}")
            count += 1

    # Preserve custom commands
    for cmd_name in backups.get("custom_commands", []):
        src = bak / "commands" / f"{cmd_name}.md"
        dest = p / ".claude" / "commands" / f"{cmd_name}.md"
        if src.is_file() and not dest.exists():
            shutil.copy2(src, dest)
            print(f"    ✅ Command preservado: {cmd_name}")
            count += 1

    # Preserve custom agents
    for agent_name in backups.get("custom_agents", []):
        src = bak / "agents" / f"{agent_name}.md"
        dest = p / ".claude" / "agents" / f"{agent_name}.md"
        if src.is_file() and not dest.exists():
            shutil.copy2(src, dest)
            print(f"    ✅ Agent preservado: {agent_name}")
            count += 1

    return count


def run_migration(project_dir: str, strategy: str = "smart") -> dict:
    """
    Execute full migration based on strategy.

    Strategies:
        - smart: Analyze and merge intelligently (default)
        - preserve: Copy all custom content without analysis
        - ignore: Don't migrate anything (just report)
    """
    analysis = full_analysis(project_dir)

    if not analysis["found"]:
        return {"success": True, "message": "Nenhum backup encontrado", "migrated": 0}

    if strategy == "ignore":
        return {"success": True, "message": "Migração ignorada conforme solicitado", "migrated": 0}

    print("\n🔄 Iniciando migração de backup...\n")
    migrated = 0

    # 1. Merge settings
    if analysis.get("settings_analysis"):
        perms = analysis["settings_analysis"]
        if perms["allow"] or perms["deny"]:
            print("  📋 Mesclando permissões...")
            if merge_settings(project_dir, perms):
                migrated += 1

    # 2. Preserve custom components
    print("  📦 Preservando componentes customizados...")
    migrated += preserve_custom_components(project_dir, analysis["backups"])

    # 3. Merge knowledge files
    if strategy == "smart":
        print("  📚 Mesclando knowledge files...")
        p = Path(project_dir)
        for key, ka in analysis.get("knowledge_analysis", {}).items():
            if ka.get("has_custom_content"):
                # Determine dest path
                subdir, filename = key.split("/")
                dest = p / ".claude" / "knowledge" / subdir / filename
                if merge_knowledge_file(ka["path"], str(dest)):
                    migrated += 1

    return {
        "success": True,
        "message": f"Migração concluída: {migrated} items processados",
        "migrated": migrated,
        "analysis": analysis,
    }


# ══════════════════════════════════════════════════════════════════════════════
# CLEANUP
# ══════════════════════════════════════════════════════════════════════════════

def cleanup_backups(project_dir: str, force: bool = False) -> dict:
    """
    Remove backup files after successful migration.

    Args:
        project_dir: Project root directory
        force: If True, delete without confirmation check

    Returns:
        dict with removed files/dirs
    """
    p = Path(project_dir)
    removed = []

    # Remove .claude.bak/
    claude_bak = p / ".claude.bak"
    if claude_bak.is_dir():
        shutil.rmtree(claude_bak)
        removed.append(".claude.bak/")
        print(f"  🗑️  Removido: .claude.bak/")

    # Remove CLAUDE.md.bak
    claude_md_bak = p / "CLAUDE.md.bak"
    if claude_md_bak.is_file():
        claude_md_bak.unlink()
        removed.append("CLAUDE.md.bak")
        print(f"  🗑️  Removido: CLAUDE.md.bak")

    # Remove any other .bak files in .claude/
    claude_dir = p / ".claude"
    if claude_dir.is_dir():
        for bak_file in claude_dir.rglob("*.bak"):
            bak_file.unlink()
            removed.append(str(bak_file.relative_to(p)))
            print(f"  🗑️  Removido: {bak_file.relative_to(p)}")

    return {
        "success": True,
        "removed": removed,
        "count": len(removed),
    }


# ══════════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Engram Backup Migration Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check if backups exist
  python3 migrate_backup.py --project-dir . --detect

  # Full analysis with recommendations
  python3 migrate_backup.py --project-dir . --analyze

  # Run smart migration
  python3 migrate_backup.py --project-dir . --migrate --strategy smart

  # Cleanup after successful migration
  python3 migrate_backup.py --project-dir . --cleanup
        """
    )
    parser.add_argument("--project-dir", default=".", help="Project root directory")
    parser.add_argument("--detect", action="store_true", help="Detect backups only")
    parser.add_argument("--analyze", action="store_true", help="Full analysis with recommendations")
    parser.add_argument("--migrate", action="store_true", help="Run migration")
    parser.add_argument("--strategy", choices=["smart", "preserve", "ignore"], default="smart",
                       help="Migration strategy (default: smart)")
    parser.add_argument("--cleanup", action="store_true", help="Remove backup files")
    parser.add_argument("--output", choices=["text", "json"], default="text")

    args = parser.parse_args()

    # Default to detect if no action specified
    if not any([args.detect, args.analyze, args.migrate, args.cleanup]):
        args.detect = True

    if args.detect:
        result = detect_backups(args.project_dir)
        if args.output == "json":
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            if result["found"]:
                print("\n🔍 Backups detectados:\n")
                if result["claude_dir_bak"]:
                    print(f"  ✅ .claude.bak/")
                if result["claude_md_bak"]:
                    print(f"  ✅ CLAUDE.md.bak")
                if result["custom_skills"]:
                    print(f"  📦 Skills customizados: {', '.join(result['custom_skills'])}")
                if result["custom_commands"]:
                    print(f"  📦 Commands customizados: {', '.join(result['custom_commands'])}")
                if result["custom_agents"]:
                    print(f"  📦 Agents customizados: {', '.join(result['custom_agents'])}")
                if result["knowledge_bak"]:
                    print(f"  📚 Knowledge files: {len(result['knowledge_bak'])}")
                print()
            else:
                print("\nℹ️  Nenhum backup encontrado.\n")

    elif args.analyze:
        result = full_analysis(args.project_dir)
        if args.output == "json":
            print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
        else:
            if not result["found"]:
                print("\nℹ️  Nenhum backup encontrado.\n")
            else:
                print("\n🔍 Análise de Backups")
                print("=" * 60)

                if result.get("claude_md_analysis"):
                    cma = result["claude_md_analysis"]
                    print(f"\n📄 CLAUDE.md.bak:")
                    if cma.get("custom_rules"):
                        print(f"   • {len(cma['custom_rules'])} regras customizadas")
                    if cma.get("custom_sections"):
                        print(f"   • {len(cma['custom_sections'])} seções customizadas")

                if result.get("settings_analysis"):
                    sa = result["settings_analysis"]
                    total = len(sa["allow"]) + len(sa["deny"])
                    if total > 0:
                        print(f"\n⚙️  settings.json.bak:")
                        print(f"   • {total} permissões customizadas")

                if result.get("knowledge_analysis"):
                    custom_knowledge = [k for k, v in result["knowledge_analysis"].items()
                                       if v.get("has_custom_content")]
                    if custom_knowledge:
                        print(f"\n📚 Knowledge com conteúdo custom:")
                        for k in custom_knowledge:
                            lines = result["knowledge_analysis"][k]["meaningful_lines"]
                            print(f"   • {k} ({lines} linhas)")

                if result.get("migration_recommendations"):
                    print(f"\n🎯 Recomendações de migração:")
                    for rec in result["migration_recommendations"]:
                        priority_icon = "🔴" if rec["priority"] == "high" else "🟡"
                        print(f"   {priority_icon} {rec['description']}")

                print()

    elif args.migrate:
        result = run_migration(args.project_dir, args.strategy)
        if args.output == "json":
            # Remove non-serializable parts
            if "analysis" in result:
                del result["analysis"]
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"\n{result['message']}\n")

    elif args.cleanup:
        result = cleanup_backups(args.project_dir)
        if args.output == "json":
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            if result["count"] > 0:
                print(f"\n✅ Cleanup concluído: {result['count']} item(s) removido(s)\n")
            else:
                print("\nℹ️  Nenhum backup para remover.\n")


if __name__ == "__main__":
    main()
