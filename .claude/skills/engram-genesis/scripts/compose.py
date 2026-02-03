#!/usr/bin/env python3
"""
Engram Genesis — Skill Composition Engine
Resolves and validates skill composition chains declared via 'composes:' in frontmatter.

Usage:
    python3 compose.py --skill my-composite-skill --project-dir .
    python3 compose.py --skill my-composite-skill --project-dir . --dry-run
    python3 compose.py --graph --project-dir .
"""

import argparse
import json
import os
import re
import sys


def parse_frontmatter(filepath: str) -> dict:
    """Extract YAML frontmatter from a SKILL.md file."""
    with open(filepath) as f:
        content = f.read()
    if not content.startswith("---"):
        return {}
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}
    fm = {}
    current_key = None
    for line in parts[1].strip().split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line and not line.startswith("- "):
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if val == "" or val == "[]":
                fm[key] = []
                current_key = key
            elif val.startswith("["):
                fm[key] = [v.strip().strip('"').strip("'") for v in val.strip("[]").split(",") if v.strip()]
                current_key = key
            else:
                fm[key] = val
                current_key = key
        elif line.startswith("- ") and current_key and isinstance(fm.get(current_key), list):
            fm[current_key].append(line[2:].strip().strip('"').strip("'"))
    return fm


def discover_skills(project_dir: str) -> dict:
    """Discover all skills and their frontmatter."""
    skills_dir = os.path.join(project_dir, ".claude", "skills")
    skills = {}
    if not os.path.isdir(skills_dir):
        return skills
    for name in os.listdir(skills_dir):
        skill_md = os.path.join(skills_dir, name, "SKILL.md")
        if os.path.isfile(skill_md):
            fm = parse_frontmatter(skill_md)
            skills[name] = {
                "path": os.path.join(skills_dir, name),
                "frontmatter": fm,
                "composes": fm.get("composes", []),
            }
    return skills


def resolve_composition(skill_name: str, skills: dict, visited: set = None) -> list:
    """
    Resolve the full composition chain for a skill.
    Returns ordered list of skill names to activate.
    Detects circular dependencies.
    """
    if visited is None:
        visited = set()

    if skill_name in visited:
        raise ValueError(f"Circular dependency detected: {skill_name} → ... → {skill_name}")

    if skill_name not in skills:
        raise ValueError(f"Skill '{skill_name}' not found")

    visited.add(skill_name)
    chain = []

    composed = skills[skill_name]["composes"]
    for sub_skill in composed:
        if sub_skill not in skills:
            raise ValueError(f"Composed skill '{sub_skill}' (required by '{skill_name}') not found")
        # Recursively resolve sub-compositions
        sub_chain = resolve_composition(sub_skill, skills, visited.copy())
        for s in sub_chain:
            if s not in chain:
                chain.append(s)

    chain.append(skill_name)
    return chain


def build_dependency_graph(skills: dict) -> dict:
    """Build a full dependency graph of all skills."""
    graph = {}
    for name, info in skills.items():
        composed = info["composes"]
        graph[name] = {
            "composes": composed,
            "composed_by": [],
            "is_leaf": len(composed) == 0,
            "is_composite": len(composed) > 0,
        }

    # Build reverse references
    for name, info in graph.items():
        for dep in info["composes"]:
            if dep in graph:
                graph[dep]["composed_by"].append(name)

    return graph


def generate_activation_plan(skill_name: str, skills: dict) -> str:
    """Generate a human-readable activation plan for a composite skill."""
    try:
        chain = resolve_composition(skill_name, skills)
    except ValueError as e:
        return f"❌ Error: {e}"

    if len(chain) <= 1:
        return f"ℹ️  '{skill_name}' is not a composite skill (no composes: declared)"

    lines = [
        f"📋 Activation Plan for '{skill_name}'",
        f"{'=' * 50}",
        f"",
        f"Composition chain ({len(chain)} skills):",
    ]

    for i, name in enumerate(chain, 1):
        is_final = name == skill_name
        icon = "🎯" if is_final else "  "
        desc = skills[name]["frontmatter"].get("description", "")[:60]
        lines.append(f"  {i}. {icon} {name}")
        if desc:
            lines.append(f"       {desc}...")

    lines.append("")
    lines.append("Execution order: " + " → ".join(chain))

    return "\n".join(lines)


def print_graph(skills: dict):
    """Print the full composition graph."""
    graph = build_dependency_graph(skills)
    composites = {k: v for k, v in graph.items() if v["is_composite"]}
    leaves = {k: v for k, v in graph.items() if v["is_leaf"] and not v["composed_by"]}
    composed = {k: v for k, v in graph.items() if v["is_leaf"] and v["composed_by"]}

    print(f"\n🧬 Skill Composition Graph")
    print(f"{'=' * 50}")

    if composites:
        print(f"\n  Composite Skills ({len(composites)}):")
        for name, info in sorted(composites.items()):
            deps = " + ".join(info["composes"])
            print(f"    🔗 {name} = [{deps}]")
    else:
        print(f"\n  No composite skills found.")

    if composed:
        print(f"\n  Skills Used in Compositions ({len(composed)}):")
        for name, info in sorted(composed.items()):
            parents = ", ".join(info["composed_by"])
            print(f"    📦 {name} (used by: {parents})")

    if leaves:
        print(f"\n  Independent Skills ({len(leaves)}):")
        for name in sorted(leaves.keys()):
            print(f"    🔹 {name}")

    # Detect circular dependencies
    print(f"\n  Dependency Check:")
    has_errors = False
    for name in composites:
        try:
            resolve_composition(name, skills)
            print(f"    ✅ {name} — chain resolves OK")
        except ValueError as e:
            print(f"    ❌ {name} — {e}")
            has_errors = True

    if not has_errors:
        print(f"\n  ✅ No circular dependencies detected")
    print()


def main():
    parser = argparse.ArgumentParser(description="Engram Skill Composition Engine")
    parser.add_argument("--skill", help="Skill to resolve composition for")
    parser.add_argument("--project-dir", default=".", help="Project root directory")
    parser.add_argument("--dry-run", action="store_true", help="Show plan without executing")
    parser.add_argument("--graph", action="store_true", help="Show full composition graph")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    skills = discover_skills(args.project_dir)

    if not skills:
        print("❌ No skills found in .claude/skills/")
        sys.exit(1)

    if args.graph:
        print_graph(skills)
        return

    if not args.skill:
        print("❌ --skill is required (or use --graph for overview)")
        sys.exit(1)

    if args.json:
        try:
            chain = resolve_composition(args.skill, skills)
            print(json.dumps({"skill": args.skill, "chain": chain, "count": len(chain)}))
        except ValueError as e:
            print(json.dumps({"error": str(e)}))
            sys.exit(1)
    else:
        print(generate_activation_plan(args.skill, skills))


if __name__ == "__main__":
    main()
