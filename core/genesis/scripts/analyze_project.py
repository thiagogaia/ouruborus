#!/usr/bin/env python3
"""
Engram Genesis — Project Analyzer
Analyzes a project and suggests which skills/agents/commands to generate.

Usage:
    python3 analyze_project.py --project-dir /path/to/project
    python3 analyze_project.py --project-dir . --output json
"""

import argparse
import json
import os
import sys
from pathlib import Path


def detect_stack(project_dir: str) -> dict:
    """Detect project stack from files and configuration."""
    stack = {
        "languages": [],
        "framework": None,
        "orm": None,
        "database": None,
        "ui": None,
        "auth": None,
        "testing": None,
        "infra": [],
        "pkg_manager": "npm",
        "has_typescript": False,
        "has_docker": False,
        "has_monorepo": False,
        "src_dir": "",
    }

    p = Path(project_dir)

    # Languages
    if (p / "package.json").exists():
        stack["languages"].append("node")
    if (p / "requirements.txt").exists() or (p / "pyproject.toml").exists():
        stack["languages"].append("python")
    if (p / "composer.json").exists():
        stack["languages"].append("php")
    if (p / "Cargo.toml").exists():
        stack["languages"].append("rust")
    if (p / "go.mod").exists():
        stack["languages"].append("go")
    if (p / "Gemfile").exists():
        stack["languages"].append("ruby")

    # TypeScript
    if (p / "tsconfig.json").exists():
        stack["has_typescript"] = True

    # Docker
    if (p / "Dockerfile").exists() or (p / "docker-compose.yml").exists():
        stack["has_docker"] = True
        stack["infra"].append("docker")

    # CI/CD
    if (p / ".gitlab-ci.yml").exists():
        stack["infra"].append("gitlab-ci")
    if (p / ".github" / "workflows").is_dir():
        stack["infra"].append("github-actions")

    # Kubernetes
    if (p / "k8s").is_dir() or (p / "kubernetes").is_dir():
        stack["infra"].append("kubernetes")
    if any(p.glob("**/kustomization.yaml")) or any(p.glob("**/kustomization.yml")):
        stack["infra"].append("kustomize")

    # ArgoCD
    if (p / "argocd").is_dir() or any(p.glob("**/argocd-app*.yaml")):
        stack["infra"].append("argocd")

    # Terraform / IaC
    if any(p.glob("*.tf")) or (p / "terraform").is_dir():
        stack["infra"].append("terraform")

    # Package manager
    if (p / "pnpm-lock.yaml").exists():
        stack["pkg_manager"] = "pnpm"
    elif (p / "yarn.lock").exists():
        stack["pkg_manager"] = "yarn"
    elif (p / "bun.lockb").exists() or (p / "bun.lock").exists():
        stack["pkg_manager"] = "bun"

    # Framework + ORM + UI + Auth from package.json
    pkg_path = p / "package.json"
    if pkg_path.exists():
        try:
            pkg = json.loads(pkg_path.read_text())
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}

            # Framework
            if "next" in deps:
                stack["framework"] = "nextjs"
            elif "@nestjs/core" in deps:
                stack["framework"] = "nestjs"
            elif "nuxt" in deps:
                stack["framework"] = "nuxt"
            elif "@angular/core" in deps:
                stack["framework"] = "angular"
            elif "svelte" in deps:
                stack["framework"] = "sveltekit"
            elif "vue" in deps:
                stack["framework"] = "vue"
            elif "react" in deps:
                stack["framework"] = "react"
            elif "express" in deps:
                stack["framework"] = "express"
            elif "fastify" in deps:
                stack["framework"] = "fastify"

            # ORM
            if "prisma" in deps or "@prisma/client" in deps:
                stack["orm"] = "prisma"
            elif "drizzle-orm" in deps:
                stack["orm"] = "drizzle"
            elif "typeorm" in deps:
                stack["orm"] = "typeorm"
            elif "sequelize" in deps:
                stack["orm"] = "sequelize"
            elif "mongoose" in deps:
                stack["orm"] = "mongoose"
                stack["database"] = "mongodb"

            # UI
            if (p / "components.json").exists():
                stack["ui"] = "shadcn"
            elif "@mui/material" in deps:
                stack["ui"] = "mui"
            elif "@chakra-ui/react" in deps:
                stack["ui"] = "chakra"
            if "tailwindcss" in deps:
                stack["infra"].append("tailwind")

            # Auth
            if "next-auth" in deps or "@auth/core" in deps:
                stack["auth"] = "nextauth"
            elif "@clerk/nextjs" in deps:
                stack["auth"] = "clerk"
            elif "better-auth" in deps:
                stack["auth"] = "better-auth"
            elif "lucia" in deps:
                stack["auth"] = "lucia"

            # Testing
            if "vitest" in deps:
                stack["testing"] = "vitest"
            elif "jest" in deps:
                stack["testing"] = "jest"
            if "@playwright/test" in deps:
                stack["testing"] = (stack["testing"] or "") + "+playwright"

            # Monorepo
            if "workspaces" in pkg or (p / "pnpm-workspace.yaml").exists():
                stack["has_monorepo"] = True

        except (json.JSONDecodeError, KeyError):
            pass

    # PHP frameworks (from composer.json)
    if "php" in stack["languages"]:
        composer_path = p / "composer.json"
        if composer_path.exists():
            try:
                composer = json.loads(composer_path.read_text())
                require = {**composer.get("require", {}), **composer.get("require-dev", {})}
                if "laravel/framework" in require:
                    stack["framework"] = "laravel"
            except (json.JSONDecodeError, KeyError):
                pass

    # Ruby frameworks (from Gemfile)
    if "ruby" in stack["languages"]:
        gemfile_path = p / "Gemfile"
        if gemfile_path.exists():
            try:
                gemfile_text = gemfile_path.read_text()
                if "rails" in gemfile_text or "railties" in gemfile_text:
                    stack["framework"] = "rails"
            except Exception:
                pass

    # Python frameworks
    if "python" in stack["languages"]:
        if (p / "manage.py").exists():
            stack["framework"] = "django"
        req = p / "requirements.txt"
        if req.exists():
            txt = req.read_text().lower()
            if "fastapi" in txt:
                stack["framework"] = "fastapi"
            elif "flask" in txt:
                stack["framework"] = "flask"

    # Database from env files
    for env_file in [".env.example", ".env.local.example", ".env"]:
        env_path = p / env_file
        if env_path.exists():
            try:
                txt = env_path.read_text().lower()
                if "postgres" in txt:
                    stack["database"] = "postgresql"
                elif "mysql" in txt:
                    stack["database"] = "mysql"
                elif "mongodb" in txt:
                    stack["database"] = "mongodb"
                elif "sqlite" in txt:
                    stack["database"] = "sqlite"
            except Exception:
                pass
            break

    # Src dir
    if (p / "src" / "app").is_dir():
        stack["src_dir"] = "src/"
    elif (p / "app").is_dir():
        stack["src_dir"] = ""
    elif (p / "src").is_dir():
        stack["src_dir"] = "src/"

    return stack


def suggest_components(stack: dict) -> dict:
    """Suggest skills, agents, and commands based on detected stack."""
    suggestions = {
        "skills": [],
        "agents": [],
        "commands": [],
        "reasoning": [],
    }

    # --- Skills ---

    # Framework-specific skills
    fw = stack.get("framework")
    if fw == "nextjs":
        suggestions["skills"].append({
            "name": "nextjs-patterns",
            "reason": "Next.js detected — Server Components, App Router, Server Actions patterns",
            "priority": "high",
        })
    elif fw == "django":
        suggestions["skills"].append({
            "name": "django-patterns",
            "reason": "Django detected — views, models, templates, management commands patterns",
            "priority": "high",
        })
    elif fw == "fastapi":
        suggestions["skills"].append({
            "name": "fastapi-patterns",
            "reason": "FastAPI detected — Pydantic models, dependency injection, async patterns",
            "priority": "high",
        })
    elif fw in ("react", "vue", "angular", "sveltekit"):
        suggestions["skills"].append({
            "name": f"{fw}-patterns",
            "reason": f"{fw} detected — component patterns, state management, routing",
            "priority": "high",
        })
    elif fw == "nestjs":
        suggestions["skills"].append({
            "name": "nestjs-patterns",
            "reason": "NestJS detected — Modules, DTOs, Guards, TypeORM/Sequelize, Swagger patterns",
            "priority": "high",
        })
    elif fw == "express":
        suggestions["skills"].append({
            "name": "express-patterns",
            "reason": "Express detected — routing, middleware, error handling patterns",
            "priority": "high",
        })
    elif fw == "fastify":
        suggestions["skills"].append({
            "name": "express-patterns",
            "reason": "Fastify detected (using Express patterns as base) — routing, plugins, validation",
            "priority": "high",
        })
    elif fw == "laravel":
        suggestions["skills"].append({
            "name": "laravel-patterns",
            "reason": "Laravel detected — Eloquent, Form Requests, Services, Queues",
            "priority": "high",
        })
    elif fw == "rails":
        suggestions["skills"].append({
            "name": "rails-patterns",
            "reason": "Rails detected — ActiveRecord, Services, Jobs, Strong Parameters patterns",
            "priority": "high",
        })
    elif fw == "flask":
        suggestions["skills"].append({
            "name": "flask-patterns",
            "reason": "Flask detected — Blueprints, Marshmallow, SQLAlchemy patterns",
            "priority": "high",
        })

    # ORM skills
    orm = stack.get("orm")
    if orm == "prisma":
        suggestions["skills"].append({
            "name": "prisma-workflow",
            "reason": "Prisma detected — schema design, migrations, query optimization",
            "priority": "high",
        })
    elif orm == "drizzle":
        suggestions["skills"].append({
            "name": "drizzle-workflow",
            "reason": "Drizzle detected — schema, push, migrations, studio",
            "priority": "high",
        })

    # Testing skill
    if stack.get("testing"):
        suggestions["skills"].append({
            "name": "test-patterns",
            "reason": f"Testing framework ({stack['testing']}) detected — test writing patterns",
            "priority": "medium",
        })

    # Auth skill
    if stack.get("auth"):
        suggestions["skills"].append({
            "name": "auth-patterns",
            "reason": f"Auth ({stack['auth']}) detected — authentication flow patterns",
            "priority": "medium",
        })

    # Docker skill
    if stack.get("has_docker"):
        suggestions["skills"].append({
            "name": "docker-workflow",
            "reason": "Docker detected — compose management, build optimization",
            "priority": "low",
        })

    # DevOps patterns (extras) — suggested when infra files detected
    infra = stack.get("infra", [])
    infra_signals = [i for i in infra if i in (
        "kubernetes", "kustomize", "argocd", "gitlab-ci", "github-actions", "terraform",
    )]
    if infra_signals:
        suggestions["skills"].append({
            "name": "devops-patterns",
            "reason": f"Infra detected ({', '.join(infra_signals)}) — K8s, CI/CD, GitOps, secrets patterns",
            "priority": "medium",
            "source": "extras",
        })

    # TypeScript skill
    if stack.get("has_typescript") and fw not in ("nextjs",):
        suggestions["skills"].append({
            "name": "typescript-strict",
            "reason": "TypeScript detected — strict typing patterns, type utilities",
            "priority": "medium",
        })

    # --- Agents ---

    # DB expert
    if stack.get("orm") or stack.get("database"):
        db_name = stack.get("database", "SQL")
        orm_name = stack.get("orm", "")
        suggestions["agents"].append({
            "name": "db-expert",
            "reason": f"Database ({db_name}) + ORM ({orm_name}) detected — needs DB specialist",
            "priority": "high",
        })

    # Architect (always)
    suggestions["agents"].append({
        "name": "architect",
        "reason": "Universal — every project benefits from architectural guidance",
        "priority": "high",
    })

    # Domain analyst (always)
    suggestions["agents"].append({
        "name": "domain-analyst",
        "reason": "Universal — discovers and documents business rules",
        "priority": "medium",
    })

    # --- Summary ---
    suggestions["reasoning"].append(
        f"Detected: {', '.join(stack['languages'])} | "
        f"Framework: {fw or 'none'} | "
        f"ORM: {orm or 'none'} | "
        f"DB: {stack.get('database', 'none')}"
    )

    return suggestions


def main():
    parser = argparse.ArgumentParser(description="Engram Project Analyzer")
    parser.add_argument("--project-dir", default=".", help="Project root directory")
    parser.add_argument("--output", choices=["text", "json"], default="text")
    args = parser.parse_args()

    stack = detect_stack(args.project_dir)
    suggestions = suggest_components(stack)

    if args.output == "json":
        result = {"stack": stack, "suggestions": suggestions}
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("\n🐍 Engram Project Analysis")
        print("=" * 50)

        print("\n📋 Stack Detectada:")
        for lang in stack["languages"]:
            print(f"  ✅ {lang}")
        if stack["framework"]:
            print(f"  ✅ Framework: {stack['framework']}")
        if stack["orm"]:
            print(f"  ✅ ORM: {stack['orm']}")
        if stack["database"]:
            print(f"  ✅ Database: {stack['database']}")
        if stack["has_typescript"]:
            print(f"  ✅ TypeScript")
        if stack["has_docker"]:
            print(f"  ✅ Docker")
        infra_extra = [i for i in stack.get("infra", []) if i != "docker"]
        for item in infra_extra:
            print(f"  ✅ Infra: {item}")

        print("\n🎯 Skills Sugeridos:")
        for s in suggestions["skills"]:
            icon = "🔴" if s["priority"] == "high" else "🟡" if s["priority"] == "medium" else "🟢"
            print(f"  {icon} {s['name']} — {s['reason']}")

        print("\n🤖 Agents Sugeridos:")
        for a in suggestions["agents"]:
            icon = "🔴" if a["priority"] == "high" else "🟡" if a["priority"] == "medium" else "🟢"
            print(f"  {icon} {a['name']} — {a['reason']}")

        if not suggestions["skills"] and not suggestions["agents"]:
            print("  ℹ️  Nenhuma sugestão específica — usando seeds universais")

        print()


if __name__ == "__main__":
    main()
