#!/usr/bin/env python3
"""
Engram Genesis — Component Generator
Generates skill/agent/command scaffolds from templates.

Usage:
    python3 generate_component.py --type skill --name api-validator --project-dir .
    python3 generate_component.py --type agent --name db-expert --project-dir .
    python3 generate_component.py --type command --name deploy --project-dir .
"""

import argparse
import json
import os
import re
import sys
from datetime import date


def load_project_context(project_dir: str) -> dict:
    """Load project context from manifest and stack detection."""
    ctx = {
        "project_name": os.path.basename(os.path.abspath(project_dir)),
        "date": date.today().isoformat(),
        "stack": [],
        "framework": "",
        "orm": "",
        "db": "",
        "pkg_manager": "npm",
    }

    # Try to read manifest
    manifest_path = os.path.join(project_dir, ".claude", "manifest.json")
    if os.path.isfile(manifest_path):
        with open(manifest_path) as f:
            manifest = json.load(f)
            ctx["manifest"] = manifest

    # Detect from package.json
    pkg_path = os.path.join(project_dir, "package.json")
    if os.path.isfile(pkg_path):
        with open(pkg_path) as f:
            pkg = json.load(f)
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        if "next" in deps:
            ctx["framework"] = "nextjs"
            ctx["stack"].append("Next.js")
        elif "react" in deps:
            ctx["framework"] = "react"
            ctx["stack"].append("React")
        elif "vue" in deps:
            ctx["framework"] = "vue"
            ctx["stack"].append("Vue")
        if "prisma" in deps or "@prisma/client" in deps:
            ctx["orm"] = "prisma"
            ctx["stack"].append("Prisma")
        if "drizzle-orm" in deps:
            ctx["orm"] = "drizzle"
            ctx["stack"].append("Drizzle")
        if "typescript" in deps:
            ctx["stack"].append("TypeScript")

    # Detect pkg manager
    if os.path.isfile(os.path.join(project_dir, "pnpm-lock.yaml")):
        ctx["pkg_manager"] = "pnpm"
    elif os.path.isfile(os.path.join(project_dir, "yarn.lock")):
        ctx["pkg_manager"] = "yarn"
    elif os.path.isfile(os.path.join(project_dir, "bun.lockb")):
        ctx["pkg_manager"] = "bun"

    # Detect Python
    if os.path.isfile(os.path.join(project_dir, "requirements.txt")):
        ctx["stack"].append("Python")
    if os.path.isfile(os.path.join(project_dir, "manage.py")):
        ctx["framework"] = "django"
        ctx["stack"].append("Django")

    return ctx


def generate_skill(name: str, project_dir: str, description: str = "") -> str:
    """Generate a skill directory with SKILL.md scaffold."""
    ctx = load_project_context(project_dir)
    skill_dir = os.path.join(project_dir, ".claude", "skills", name)

    if os.path.exists(skill_dir):
        print(f"⚠️  Skill '{name}' already exists at {skill_dir}")
        return skill_dir

    os.makedirs(skill_dir, exist_ok=True)

    desc_placeholder = description or f"[TODO: Descreva o que este skill faz e quando ativá-lo. Mínimo 50 caracteres. Inclua triggers explícitos.]"
    stack_note = f"\nStack detectada: {', '.join(ctx['stack'])}" if ctx["stack"] else ""

    content = f"""---
name: {name}
description: {desc_placeholder}
---

# {name.replace('-', ' ').title()}
{stack_note}

## Propósito
[TODO: 1-2 parágrafos explicando o que este skill resolve]

## Workflow

1. [TODO: Primeiro passo]
2. [TODO: Segundo passo]
3. [TODO: Passo final]

## Regras
- [TODO: Guardrail 1]
- [TODO: Guardrail 2]

## Output Esperado
[TODO: Formato de resposta esperado]
"""
    with open(os.path.join(skill_dir, "SKILL.md"), "w") as f:
        f.write(content)

    print(f"✅ Skill scaffold created: {skill_dir}/")
    print(f"   → Edit SKILL.md to customize for your project")
    return skill_dir


def generate_agent(name: str, project_dir: str, description: str = "") -> str:
    """Generate an agent .md file scaffold."""
    ctx = load_project_context(project_dir)
    agents_dir = os.path.join(project_dir, ".claude", "agents")
    os.makedirs(agents_dir, exist_ok=True)
    agent_path = os.path.join(agents_dir, f"{name}.md")

    if os.path.exists(agent_path):
        print(f"⚠️  Agent '{name}' already exists at {agent_path}")
        return agent_path

    desc_placeholder = description or f"[TODO: Descreva a especialidade deste agent e quando invocá-lo. Mínimo 50 caracteres.]"

    content = f"""---
name: {name}
description: {desc_placeholder}
tools:
  - Read
  - Grep
  - Glob
---

Você é um especialista em {name.replace('-', ' ')}.

## Responsabilidades
- [TODO: Responsabilidade 1]
- [TODO: Responsabilidade 2]

## Regras
- SEMPRE consulte os knowledge files antes de decidir
- NUNCA modifique arquitetura sem registrar em ADR_LOG.md
- [TODO: Regras específicas deste agent]

## Output Esperado
[TODO: Formato de resposta esperado]
"""
    with open(agent_path, "w") as f:
        f.write(content)

    print(f"✅ Agent scaffold created: {agent_path}")
    print(f"   → Edit to customize for your project")
    return agent_path


def generate_command(name: str, project_dir: str, description: str = "") -> str:
    """Generate a command .md file scaffold."""
    commands_dir = os.path.join(project_dir, ".claude", "commands")
    os.makedirs(commands_dir, exist_ok=True)
    cmd_path = os.path.join(commands_dir, f"{name}.md")

    if os.path.exists(cmd_path):
        print(f"⚠️  Command '{name}' already exists at {cmd_path}")
        return cmd_path

    content = f"""[TODO: Instruções para o comando /{name}]

Se $ARGUMENTS fornecido, use como contexto.

1. [TODO: Passo 1]
2. [TODO: Passo 2]
3. Resuma o resultado em formato conciso.
"""
    with open(cmd_path, "w") as f:
        f.write(content)

    print(f"✅ Command scaffold created: {cmd_path}")
    print(f"   → Edit to add actual instructions")
    return cmd_path


def main():
    parser = argparse.ArgumentParser(description="Engram Component Generator")
    parser.add_argument("--type", required=True, choices=["skill", "agent", "command"])
    parser.add_argument("--name", required=True, help="Component name (kebab-case)")
    parser.add_argument("--project-dir", default=".", help="Project root directory")
    parser.add_argument("--description", default="", help="Optional description")
    args = parser.parse_args()

    # Validate name
    if not re.match(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$", args.name):
        print(f"❌ Name '{args.name}' must be kebab-case (e.g., my-skill-name)")
        sys.exit(1)

    generators = {
        "skill": generate_skill,
        "agent": generate_agent,
        "command": generate_command,
    }

    generators[args.type](args.name, args.project_dir, args.description)


if __name__ == "__main__":
    main()
