#!/usr/bin/env python3
"""
Engram Evolution — Curriculum Engine
Analyzes the project's skill coverage and suggests what to learn/create next.
Compares installed skills against detected stack needs and usage patterns.

Usage:
    python3 curriculum.py --project-dir .
    python3 curriculum.py --project-dir . --json
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path


def load_manifest(project_dir: str) -> dict:
    path = os.path.join(project_dir, ".claude", "manifest.json")
    if os.path.isfile(path):
        with open(path) as f:
            return json.load(f)
    return {"components": {"skills": {}, "agents": {}, "commands": {}}}


def load_activation_log(project_dir: str) -> list:
    path = os.path.join(project_dir, ".claude", "evolution-activations.json")
    if os.path.isfile(path):
        with open(path) as f:
            return json.load(f)
    return []


def detect_stack_simple(project_dir: str) -> dict:
    """Lightweight stack detection (not as thorough as analyze_project.py)."""
    stack = {"languages": [], "framework": None, "orm": None, "db": None,
             "has_typescript": False, "has_docker": False, "has_tests": False,
             "ui": None, "auth": None}

    pkg_path = os.path.join(project_dir, "package.json")
    if os.path.isfile(pkg_path):
        stack["languages"].append("node")
        try:
            pkg = json.loads(Path(pkg_path).read_text())
            all_deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            if "next" in all_deps: stack["framework"] = "nextjs"
            elif "nuxt" in all_deps: stack["framework"] = "nuxt"
            elif "vue" in all_deps: stack["framework"] = "vue"
            elif "react" in all_deps: stack["framework"] = "react"
            elif "express" in all_deps: stack["framework"] = "express"
            if "prisma" in str(all_deps) or "@prisma/client" in all_deps: stack["orm"] = "prisma"
            elif "drizzle-orm" in all_deps: stack["orm"] = "drizzle"
            if "vitest" in all_deps or "jest" in all_deps: stack["has_tests"] = True
            if "tailwindcss" in all_deps: stack["ui"] = "tailwind"
            if "next-auth" in all_deps or "@auth/core" in all_deps: stack["auth"] = "nextauth"
            elif "better-auth" in all_deps: stack["auth"] = "better-auth"
        except Exception:
            pass

    if os.path.isfile(os.path.join(project_dir, "requirements.txt")) or \
       os.path.isfile(os.path.join(project_dir, "pyproject.toml")):
        stack["languages"].append("python")
        if os.path.isfile(os.path.join(project_dir, "manage.py")):
            stack["framework"] = "django"
    if os.path.isfile(os.path.join(project_dir, "composer.json")):
        stack["languages"].append("php")
        if os.path.isfile(os.path.join(project_dir, "artisan")):
            stack["framework"] = "laravel"
    if os.path.isfile(os.path.join(project_dir, "tsconfig.json")):
        stack["has_typescript"] = True
    if os.path.isfile(os.path.join(project_dir, "Dockerfile")) or \
       os.path.isfile(os.path.join(project_dir, "docker-compose.yml")):
        stack["has_docker"] = True

    env_path = os.path.join(project_dir, ".env.example")
    if os.path.isfile(env_path):
        content = Path(env_path).read_text().lower()
        if "postgres" in content: stack["db"] = "postgresql"
        elif "mysql" in content: stack["db"] = "mysql"
        elif "mongodb" in content: stack["db"] = "mongodb"

    return stack


def get_ideal_skills(stack: dict) -> list:
    """What skills SHOULD exist for this stack."""
    ideal = []

    # Universal (always needed)
    ideal.append({"name": "project-analyzer", "category": "core", "reason": "Codebase analysis"})
    ideal.append({"name": "knowledge-manager", "category": "core", "reason": "Feedback loop"})
    ideal.append({"name": "priority-engine", "category": "core", "reason": "Prioritization"})
    ideal.append({"name": "code-reviewer", "category": "core", "reason": "Code quality"})
    ideal.append({"name": "domain-expert", "category": "core", "reason": "Business domain"})

    # Framework-specific
    fw = stack.get("framework")
    if fw:
        ideal.append({"name": f"{fw}-patterns", "category": "framework",
                      "reason": f"{fw} best practices"})

    # ORM/DB
    if stack.get("orm"):
        ideal.append({"name": f"{stack['orm']}-workflow", "category": "data",
                      "reason": f"{stack['orm']} migrations, queries, schema"})
    if stack.get("db"):
        pass  # db-expert agent covers this

    # Testing
    if stack.get("has_tests"):
        ideal.append({"name": "test-patterns", "category": "quality",
                      "reason": "Test writing patterns"})

    # Auth
    if stack.get("auth"):
        ideal.append({"name": "auth-patterns", "category": "security",
                      "reason": f"{stack['auth']} authentication flows"})

    # Docker
    if stack.get("has_docker"):
        ideal.append({"name": "docker-workflow", "category": "infra",
                      "reason": "Container management"})

    return ideal


def get_ideal_agents(stack: dict) -> list:
    """What agents SHOULD exist."""
    ideal = [
        {"name": "architect", "reason": "Architectural decisions"},
        {"name": "domain-analyst", "reason": "Business domain analysis"},
    ]
    if stack.get("db") or stack.get("orm"):
        ideal.append({"name": "db-expert", "reason": "Database optimization"})
    return ideal


def analyze_usage_gaps(manifest: dict) -> list:
    """Detect skills that exist but are never used."""
    gaps = []
    skills = manifest.get("components", {}).get("skills", {})
    for name, info in skills.items():
        activations = info.get("activations", 0)
        if activations == 0:
            gaps.append({"name": name, "type": "unused",
                        "message": f"Installed but never activated — consider using or archiving"})
    return gaps


def generate_curriculum(project_dir: str) -> dict:
    """Generate a learning curriculum for the project."""
    stack = detect_stack_simple(project_dir)
    manifest = load_manifest(project_dir)
    installed_skills = set(manifest.get("components", {}).get("skills", {}).keys())
    installed_agents = set()

    agents_dir = os.path.join(project_dir, ".claude", "agents")
    if os.path.isdir(agents_dir):
        for f in os.listdir(agents_dir):
            if f.endswith(".md"):
                installed_agents.add(f.replace(".md", ""))

    # Also check skills directory directly
    skills_dir = os.path.join(project_dir, ".claude", "skills")
    if os.path.isdir(skills_dir):
        for d in os.listdir(skills_dir):
            if os.path.isdir(os.path.join(skills_dir, d)):
                installed_skills.add(d)

    ideal_skills = get_ideal_skills(stack)
    ideal_agents = get_ideal_agents(stack)
    usage_gaps = analyze_usage_gaps(manifest)

    # Missing skills
    missing_skills = [s for s in ideal_skills if s["name"] not in installed_skills]
    present_skills = [s for s in ideal_skills if s["name"] in installed_skills]

    # Missing agents
    missing_agents = [a for a in ideal_agents if a["name"] not in installed_agents]

    # Coverage
    total_ideal = len(ideal_skills) + len(ideal_agents)
    total_present = len(present_skills) + (len(ideal_agents) - len(missing_agents))
    coverage = int((total_present / max(total_ideal, 1)) * 100)

    return {
        "stack": stack,
        "coverage": coverage,
        "missing_skills": missing_skills,
        "missing_agents": missing_agents,
        "usage_gaps": usage_gaps,
        "installed_skills": list(installed_skills),
        "ideal_skills": ideal_skills,
    }


def print_curriculum(project_dir: str):
    """Print the curriculum report."""
    result = generate_curriculum(project_dir)

    coverage = result["coverage"]
    if coverage >= 90:
        emoji = "🟢"
    elif coverage >= 60:
        emoji = "🟡"
    else:
        emoji = "🔴"

    print(f"\n📚 Engram Curriculum")
    print(f"{'=' * 50}")
    print(f"  {emoji} Skill Coverage: {coverage}%")
    print(f"  Installed: {len(result['installed_skills'])} skills")

    if result["missing_skills"]:
        print(f"\n  🎯 Missing Skills ({len(result['missing_skills'])}):")
        for s in result["missing_skills"]:
            print(f"    🔴 {s['name']} ({s['category']})")
            print(f"       {s['reason']}")
            print(f"       → /create skill {s['name']}")

    if result["missing_agents"]:
        print(f"\n  🤖 Missing Agents ({len(result['missing_agents'])}):")
        for a in result["missing_agents"]:
            print(f"    🔴 {a['name']}")
            print(f"       {a['reason']}")

    if result["usage_gaps"]:
        print(f"\n  ⚠️  Usage Gaps ({len(result['usage_gaps'])}):")
        for g in result["usage_gaps"]:
            print(f"    📦 {g['name']}: {g['message']}")

    if not result["missing_skills"] and not result["missing_agents"]:
        print(f"\n  ✅ Full coverage! All recommended skills and agents are installed.")
        if result["usage_gaps"]:
            print(f"     Consider activating unused skills or archiving them.")

    # Suggest next action
    print(f"\n  💡 Next Steps:")
    if result["missing_skills"]:
        top = result["missing_skills"][0]
        print(f"     1. Create: /create skill {top['name']}")
    if result["usage_gaps"]:
        top = result["usage_gaps"][0]
        print(f"     2. Use or archive: {top['name']}")
    if not result["missing_skills"] and not result["usage_gaps"]:
        print(f"     Keep using /learn to evolve the system.")
    print()


def main():
    parser = argparse.ArgumentParser(description="Engram Curriculum Engine")
    parser.add_argument("--project-dir", default=".")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.json:
        result = generate_curriculum(args.project_dir)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print_curriculum(args.project_dir)


if __name__ == "__main__":
    main()
