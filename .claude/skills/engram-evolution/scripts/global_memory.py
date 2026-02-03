#!/usr/bin/env python3
"""
Engram — Global Memory (Multi-Project)
Manages cross-project learnings stored in ~/.engram/.
Skills, patterns, and experiences that transfer between projects.

Usage:
    python3 global_memory.py init
    python3 global_memory.py export-pattern --name PAT-005 --project-dir .
    python3 global_memory.py export-experience --name EXP-003 --project-dir .
    python3 global_memory.py export-skill --name api-validator --project-dir .
    python3 global_memory.py import-skill --name api-validator --project-dir .
    python3 global_memory.py list
    python3 global_memory.py search --query "api validation"
"""

import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path


GLOBAL_DIR = os.path.expanduser("~/.engram")
GLOBAL_MANIFEST = os.path.join(GLOBAL_DIR, "global-manifest.json")
GLOBAL_PATTERNS = os.path.join(GLOBAL_DIR, "patterns.json")
GLOBAL_EXPERIENCES = os.path.join(GLOBAL_DIR, "experiences.json")
GLOBAL_SKILLS = os.path.join(GLOBAL_DIR, "skills")


def ensure_global_dir():
    """Initialize ~/.engram/ if it doesn't exist."""
    os.makedirs(GLOBAL_SKILLS, exist_ok=True)

    if not os.path.isfile(GLOBAL_MANIFEST):
        manifest = {
            "created_at": datetime.now().isoformat(),
            "projects": {},
            "exported_patterns": 0,
            "exported_experiences": 0,
            "exported_skills": 0,
        }
        with open(GLOBAL_MANIFEST, "w") as f:
            json.dump(manifest, f, indent=2)

    if not os.path.isfile(GLOBAL_PATTERNS):
        with open(GLOBAL_PATTERNS, "w") as f:
            json.dump([], f)

    if not os.path.isfile(GLOBAL_EXPERIENCES):
        with open(GLOBAL_EXPERIENCES, "w") as f:
            json.dump([], f)


def load_json(path: str) -> any:
    with open(path) as f:
        return json.load(f)


def save_json(path: str, data: any):
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_project_name(project_dir: str) -> str:
    pkg = os.path.join(project_dir, "package.json")
    if os.path.isfile(pkg):
        try:
            return json.loads(Path(pkg).read_text()).get("name", "")
        except Exception:
            pass
    return os.path.basename(os.path.abspath(project_dir))


def cmd_init():
    """Initialize global memory."""
    ensure_global_dir()
    print(f"✅ Global memory initialized at {GLOBAL_DIR}")
    print(f"   Patterns: {GLOBAL_PATTERNS}")
    print(f"   Experiences: {GLOBAL_EXPERIENCES}")
    print(f"   Skills: {GLOBAL_SKILLS}/")


def cmd_export_pattern(name: str, project_dir: str):
    """Export a pattern from project's PATTERNS.md to global memory."""
    ensure_global_dir()
    patterns_file = os.path.join(project_dir, ".claude", "knowledge", "patterns", "PATTERNS.md")
    if not os.path.isfile(patterns_file):
        print(f"❌ PATTERNS.md not found in {project_dir}")
        sys.exit(1)

    content = Path(patterns_file).read_text()

    # Find the pattern by name
    pattern_match = re.search(
        rf"### {re.escape(name)}:.*?(?=\n### |\Z)",
        content,
        re.DOTALL
    )
    if not pattern_match:
        print(f"❌ Pattern '{name}' not found in PATTERNS.md")
        sys.exit(1)

    pattern_text = pattern_match.group(0).strip()
    project_name = get_project_name(project_dir)

    entry = {
        "id": name,
        "content": pattern_text,
        "source_project": project_name,
        "exported_at": datetime.now().isoformat(),
    }

    patterns = load_json(GLOBAL_PATTERNS)
    # Upsert
    patterns = [p for p in patterns if p["id"] != name]
    patterns.append(entry)
    save_json(GLOBAL_PATTERNS, patterns)

    manifest = load_json(GLOBAL_MANIFEST)
    manifest["exported_patterns"] = len(patterns)
    save_json(GLOBAL_MANIFEST, manifest)

    print(f"✅ Exported pattern '{name}' from {project_name} to global memory")


def cmd_export_experience(name: str, project_dir: str):
    """Export an experience from EXPERIENCE_LIBRARY.md to global memory."""
    ensure_global_dir()
    exp_file = os.path.join(project_dir, ".claude", "knowledge", "experiences", "EXPERIENCE_LIBRARY.md")
    if not os.path.isfile(exp_file):
        print(f"❌ EXPERIENCE_LIBRARY.md not found")
        sys.exit(1)

    content = Path(exp_file).read_text()
    exp_match = re.search(
        rf"### {re.escape(name)}:.*?(?=\n### |\Z)",
        content,
        re.DOTALL
    )
    if not exp_match:
        print(f"❌ Experience '{name}' not found")
        sys.exit(1)

    entry = {
        "id": name,
        "content": exp_match.group(0).strip(),
        "source_project": get_project_name(project_dir),
        "exported_at": datetime.now().isoformat(),
    }

    experiences = load_json(GLOBAL_EXPERIENCES)
    experiences = [e for e in experiences if e["id"] != name]
    experiences.append(entry)
    save_json(GLOBAL_EXPERIENCES, experiences)

    manifest = load_json(GLOBAL_MANIFEST)
    manifest["exported_experiences"] = len(experiences)
    save_json(GLOBAL_MANIFEST, manifest)

    print(f"✅ Exported experience '{name}' to global memory")


def cmd_export_skill(name: str, project_dir: str):
    """Export a skill directory to global memory."""
    ensure_global_dir()
    skill_src = os.path.join(project_dir, ".claude", "skills", name)
    if not os.path.isdir(skill_src):
        print(f"❌ Skill '{name}' not found in {project_dir}")
        sys.exit(1)

    skill_dest = os.path.join(GLOBAL_SKILLS, name)
    if os.path.exists(skill_dest):
        shutil.rmtree(skill_dest)
    shutil.copytree(skill_src, skill_dest)

    # Add metadata
    meta = {
        "name": name,
        "source_project": get_project_name(project_dir),
        "exported_at": datetime.now().isoformat(),
    }
    with open(os.path.join(skill_dest, ".export-meta.json"), "w") as f:
        json.dump(meta, f, indent=2)

    manifest = load_json(GLOBAL_MANIFEST)
    manifest["exported_skills"] = len([
        d for d in os.listdir(GLOBAL_SKILLS)
        if os.path.isdir(os.path.join(GLOBAL_SKILLS, d))
    ])
    save_json(GLOBAL_MANIFEST, manifest)

    print(f"✅ Exported skill '{name}' to ~/.engram/skills/{name}/")


def cmd_import_skill(name: str, project_dir: str):
    """Import a skill from global memory into a project."""
    skill_src = os.path.join(GLOBAL_SKILLS, name)
    if not os.path.isdir(skill_src):
        print(f"❌ Skill '{name}' not found in global memory")
        available = [d for d in os.listdir(GLOBAL_SKILLS) if os.path.isdir(os.path.join(GLOBAL_SKILLS, d))]
        if available:
            print(f"   Available: {', '.join(available)}")
        sys.exit(1)

    skill_dest = os.path.join(project_dir, ".claude", "skills", name)
    if os.path.exists(skill_dest):
        print(f"⚠️  Skill '{name}' already exists in project. Overwrite? (y/N)")
        # Non-interactive: skip
        print(f"   Skipped. Remove existing skill first.")
        return

    shutil.copytree(skill_src, skill_dest)
    # Remove export metadata
    meta_file = os.path.join(skill_dest, ".export-meta.json")
    if os.path.exists(meta_file):
        os.remove(meta_file)

    print(f"✅ Imported skill '{name}' from global memory")
    print(f"   → Register: python3 .claude/skills/engram-genesis/scripts/register.py --type skill --name {name}")


def cmd_list():
    """List everything in global memory."""
    ensure_global_dir()

    print(f"\n🌐 Engram Global Memory (~/.engram/)")
    print(f"{'=' * 50}")

    # Skills
    skills = [d for d in os.listdir(GLOBAL_SKILLS) if os.path.isdir(os.path.join(GLOBAL_SKILLS, d))]
    print(f"\n  🎯 Skills ({len(skills)}):")
    for sk in sorted(skills):
        meta_path = os.path.join(GLOBAL_SKILLS, sk, ".export-meta.json")
        source = "?"
        if os.path.isfile(meta_path):
            meta = load_json(meta_path)
            source = meta.get("source_project", "?")
        print(f"    📦 {sk} (from: {source})")

    # Patterns
    patterns = load_json(GLOBAL_PATTERNS)
    print(f"\n  📝 Patterns ({len(patterns)}):")
    for p in patterns:
        first_line = p["content"].split("\n")[0][:60]
        print(f"    • {p['id']}: {first_line}")

    # Experiences
    experiences = load_json(GLOBAL_EXPERIENCES)
    print(f"\n  💡 Experiences ({len(experiences)}):")
    for e in experiences:
        first_line = e["content"].split("\n")[0][:60]
        print(f"    • {e['id']}: {first_line}")

    print()


def cmd_search(query: str):
    """Search across all global memory."""
    ensure_global_dir()
    query_lower = query.lower()
    results = []

    # Search patterns
    for p in load_json(GLOBAL_PATTERNS):
        if query_lower in p["content"].lower():
            results.append(("pattern", p["id"], p["content"].split("\n")[0][:80]))

    # Search experiences
    for e in load_json(GLOBAL_EXPERIENCES):
        if query_lower in e["content"].lower():
            results.append(("experience", e["id"], e["content"].split("\n")[0][:80]))

    # Search skills
    for sk in os.listdir(GLOBAL_SKILLS):
        skill_md = os.path.join(GLOBAL_SKILLS, sk, "SKILL.md")
        if os.path.isfile(skill_md):
            content = Path(skill_md).read_text().lower()
            if query_lower in content:
                results.append(("skill", sk, f"Skill directory in ~/.engram/skills/{sk}/"))

    if results:
        print(f"\n🔍 Search results for '{query}' ({len(results)} found):")
        for rtype, name, preview in results:
            print(f"  [{rtype:10s}] {name}: {preview}")
    else:
        print(f"\n🔍 No results for '{query}'")
    print()


def main():
    parser = argparse.ArgumentParser(description="Engram Global Memory")
    parser.add_argument("command", choices=[
        "init", "export-pattern", "export-experience", "export-skill",
        "import-skill", "list", "search"
    ])
    parser.add_argument("--name", help="Item name")
    parser.add_argument("--project-dir", default=".", help="Project root")
    parser.add_argument("--query", help="Search query")
    args = parser.parse_args()

    commands = {
        "init": lambda: cmd_init(),
        "export-pattern": lambda: cmd_export_pattern(args.name, args.project_dir),
        "export-experience": lambda: cmd_export_experience(args.name, args.project_dir),
        "export-skill": lambda: cmd_export_skill(args.name, args.project_dir),
        "import-skill": lambda: cmd_import_skill(args.name, args.project_dir),
        "list": lambda: cmd_list(),
        "search": lambda: cmd_search(args.query or ""),
    }

    try:
        commands[args.command]()
    except TypeError as e:
        print(f"❌ Missing required argument: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
