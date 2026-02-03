#!/usr/bin/env python3
"""
Engram — Doctor (Health Check)
Validates the entire Engram installation: structure, components, knowledge freshness.

Usage:
    python3 doctor.py --project-dir .
    python3 doctor.py --project-dir . --fix
    python3 doctor.py --project-dir . --json
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Reuse validate from genesis
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
GENESIS_SCRIPTS = os.path.join(SCRIPT_DIR, "..", "..", "engram-genesis", "scripts")
# At install time the path is relative to .claude/skills/
INSTALLED_GENESIS = None


def find_validate_module(project_dir: str):
    """Find validate.py in the installed genesis skill."""
    candidates = [
        os.path.join(project_dir, ".claude", "skills", "engram-genesis", "scripts", "validate.py"),
        os.path.join(GENESIS_SCRIPTS, "validate.py"),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None


class Check:
    def __init__(self, name: str, status: str, message: str, fix: str = ""):
        self.name = name
        self.status = status  # "ok" | "warn" | "error"
        self.message = message
        self.fix = fix

    def icon(self) -> str:
        return {"ok": "✅", "warn": "⚠️", "error": "❌"}.get(self.status, "?")

    def __str__(self):
        base = f"  {self.icon()} {self.name}: {self.message}"
        if self.fix:
            base += f"\n     💡 Fix: {self.fix}"
        return base

    def to_dict(self) -> dict:
        return {"name": self.name, "status": self.status, "message": self.message, "fix": self.fix}


def check_structure(project_dir: str) -> list:
    """Check that all required files and directories exist."""
    checks = []
    p = Path(project_dir)

    required = {
        "CLAUDE.md": "Main instructions file",
        ".claude/settings.json": "Permissions config",
        ".claude/manifest.json": "Component registry",
    }

    required_dirs = {
        ".claude/skills": "Skills directory",
        ".claude/commands": "Commands directory",
        ".claude/schemas": "Schema definitions (DNA)",
        ".claude/knowledge/context": "Context knowledge",
        ".claude/knowledge/priorities": "Priorities knowledge",
        ".claude/knowledge/patterns": "Patterns knowledge",
        ".claude/knowledge/decisions": "Decisions knowledge",
        ".claude/knowledge/domain": "Domain knowledge",
        ".claude/knowledge/experiences": "Experiences knowledge",
    }

    for file, desc in required.items():
        if (p / file).exists():
            checks.append(Check(desc, "ok", f"{file} exists"))
        else:
            checks.append(Check(desc, "error", f"{file} missing",
                                f"Run setup.sh or create manually"))

    for dir_path, desc in required_dirs.items():
        if (p / dir_path).is_dir():
            checks.append(Check(desc, "ok", f"{dir_path}/ exists"))
        else:
            checks.append(Check(desc, "error", f"{dir_path}/ missing",
                                f"Run setup.sh to recreate"))

    # Check core skills
    core_skills = ["engram-genesis", "engram-evolution"]
    for skill in core_skills:
        skill_path = p / ".claude" / "skills" / skill / "SKILL.md"
        if skill_path.exists():
            checks.append(Check(f"Core skill: {skill}", "ok", "Installed"))
        else:
            checks.append(Check(f"Core skill: {skill}", "error", "Missing",
                                "Run setup.sh --update"))

    return checks


def check_knowledge_freshness(project_dir: str) -> list:
    """Check if knowledge files are recent."""
    checks = []
    p = Path(project_dir)
    now = datetime.now()

    knowledge_files = {
        ".claude/knowledge/context/CURRENT_STATE.md": "CURRENT_STATE",
        ".claude/knowledge/priorities/PRIORITY_MATRIX.md": "PRIORITY_MATRIX",
        ".claude/knowledge/patterns/PATTERNS.md": "PATTERNS",
        ".claude/knowledge/decisions/ADR_LOG.md": "ADR_LOG",
        ".claude/knowledge/domain/DOMAIN.md": "DOMAIN",
        ".claude/knowledge/experiences/EXPERIENCE_LIBRARY.md": "EXPERIENCE_LIBRARY",
    }

    for file_path, name in knowledge_files.items():
        full_path = p / file_path
        if not full_path.exists():
            checks.append(Check(f"Knowledge: {name}", "error", "File missing",
                                "Run /init-engram to create"))
            continue

        # Check file size
        size = full_path.stat().st_size
        if size < 50:
            checks.append(Check(f"Knowledge: {name}", "warn", "File nearly empty",
                                "Run /init-engram or /learn to populate"))
            continue

        # Check modification date
        mtime = datetime.fromtimestamp(full_path.stat().st_mtime)
        age_days = (now - mtime).days

        if age_days > 14:
            checks.append(Check(f"Knowledge: {name}", "warn",
                                f"Last updated {age_days} days ago",
                                "Run /learn to refresh"))
        elif age_days > 7:
            checks.append(Check(f"Knowledge: {name}", "ok",
                                f"Updated {age_days} days ago (consider /learn)"))
        else:
            checks.append(Check(f"Knowledge: {name}", "ok",
                                f"Fresh (updated {age_days}d ago)"))

    return checks


def check_components(project_dir: str) -> list:
    """Validate all installed components against schemas."""
    checks = []
    p = Path(project_dir)

    # Validate skills
    skills_dir = p / ".claude" / "skills"
    if skills_dir.is_dir():
        skill_count = 0
        valid_count = 0
        for skill_name in sorted(os.listdir(skills_dir)):
            skill_path = skills_dir / skill_name
            if not skill_path.is_dir():
                continue
            skill_md = skill_path / "SKILL.md"
            if not skill_md.exists():
                checks.append(Check(f"Skill: {skill_name}", "error",
                                    "Missing SKILL.md"))
                skill_count += 1
                continue

            # Basic validation inline (avoid import complexity)
            content = skill_md.read_text()
            skill_count += 1
            issues = []

            if not content.startswith("---"):
                issues.append("Missing frontmatter")
            else:
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    fm_text = parts[1]
                    if "name:" not in fm_text:
                        issues.append("Missing name: in frontmatter")
                    if "description:" not in fm_text:
                        issues.append("Missing description: in frontmatter")

            body_lines = content.split("---", 2)[-1].split("\n") if "---" in content else content.split("\n")
            if len(body_lines) > 500:
                issues.append(f"Body too long ({len(body_lines)} lines)")

            if issues:
                checks.append(Check(f"Skill: {skill_name}", "warn",
                                    "; ".join(issues)))
            else:
                valid_count += 1

        checks.append(Check("Skills summary", "ok",
                            f"{valid_count}/{skill_count} skills valid"))

    # Validate agents
    agents_dir = p / ".claude" / "agents"
    if agents_dir.is_dir():
        for agent_file in sorted(agents_dir.glob("*.md")):
            content = agent_file.read_text()
            agent_name = agent_file.stem
            if not content.startswith("---"):
                checks.append(Check(f"Agent: {agent_name}", "warn",
                                    "Missing frontmatter"))
            else:
                checks.append(Check(f"Agent: {agent_name}", "ok", "Valid"))

    # Validate manifest
    manifest_path = p / ".claude" / "manifest.json"
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text())
            comp_count = sum(len(v) for v in manifest.get("components", {}).values())
            checks.append(Check("Manifest", "ok",
                                f"Valid ({comp_count} components registered)"))

            # Check manifest sync — are registered skills actually present?
            registered_skills = manifest.get("components", {}).get("skills", {})
            for sk_name in registered_skills:
                if not (skills_dir / sk_name / "SKILL.md").exists():
                    checks.append(Check(f"Manifest sync: {sk_name}", "warn",
                                        "Registered but not found on disk",
                                        "Run /doctor --fix or re-register"))

            # Check unregistered skills
            if skills_dir.is_dir():
                for sk_name in os.listdir(skills_dir):
                    if (skills_dir / sk_name / "SKILL.md").exists():
                        if sk_name not in registered_skills:
                            checks.append(Check(f"Manifest sync: {sk_name}", "warn",
                                                "Installed but not registered in manifest",
                                                f"register.py --type skill --name {sk_name}"))

        except json.JSONDecodeError:
            checks.append(Check("Manifest", "error", "Invalid JSON"))

    return checks


def check_consistency(project_dir: str) -> list:
    """Cross-check settings, agents, skills for consistency."""
    checks = []
    p = Path(project_dir)

    settings_path = p / ".claude" / "settings.json"
    if not settings_path.exists():
        return checks

    try:
        settings = json.loads(settings_path.read_text())
    except json.JSONDecodeError:
        checks.append(Check("Settings.json", "error", "Invalid JSON"))
        return checks

    allowed = settings.get("permissions", {}).get("allow", [])

    # Check if agents reference tools that are in settings
    agents_dir = p / ".claude" / "agents"
    if agents_dir.is_dir():
        for agent_file in agents_dir.glob("*.md"):
            content = agent_file.read_text()
            if "tools:" in content:
                # Extract tools from frontmatter
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    fm = parts[1]
                    in_tools = False
                    for line in fm.split("\n"):
                        if line.strip().startswith("tools:"):
                            in_tools = True
                            continue
                        if in_tools and line.strip().startswith("- "):
                            tool = line.strip()[2:].strip()
                            if tool not in allowed:
                                checks.append(Check(
                                    f"Agent {agent_file.stem} tool '{tool}'",
                                    "warn",
                                    f"Tool '{tool}' not in settings.json allow list"
                                ))
                        elif in_tools and not line.strip().startswith("- "):
                            in_tools = False

    # Check engram version
    version_file = p / ".claude" / ".engram-version"
    if version_file.exists():
        ver = version_file.read_text().strip()
        checks.append(Check("Engram version", "ok", f"v{ver}"))
    else:
        checks.append(Check("Engram version", "warn", "Version file missing"))

    # Check runtime components needing evaluation
    manifest_path = p / ".claude" / "manifest.json"
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text())
            runtime_count = 0
            for comp_type, comps in manifest.get("components", {}).items():
                for name, info in comps.items():
                    if info.get("source") == "runtime" and info.get("health") != "archived":
                        runtime_count += 1
                        acts = info.get("activations", 0)
                        if acts <= 1:
                            checks.append(Check(
                                f"Runtime: {name}", "warn",
                                f"Created at runtime, only {acts} use(s) — evaluate with /learn",
                                "Run /learn to decide: keep or archive"))
            if runtime_count > 0:
                checks.append(Check("Runtime components", "ok",
                                    f"{runtime_count} runtime component(s) pending evaluation"))
        except (json.JSONDecodeError, KeyError):
            pass

    return checks


def run_doctor(project_dir: str, output_json: bool = False, auto_fix: bool = False):
    """Run all health checks."""
    all_checks = []

    all_checks.extend(check_structure(project_dir))
    all_checks.extend(check_knowledge_freshness(project_dir))
    all_checks.extend(check_components(project_dir))
    all_checks.extend(check_consistency(project_dir))

    ok = sum(1 for c in all_checks if c.status == "ok")
    warn = sum(1 for c in all_checks if c.status == "warn")
    error = sum(1 for c in all_checks if c.status == "error")
    total = len(all_checks)
    score = int((ok / max(total, 1)) * 100)

    if score >= 90:
        health_emoji = "🟢"
    elif score >= 70:
        health_emoji = "🟡"
    else:
        health_emoji = "🔴"

    if output_json:
        result = {
            "score": score,
            "health": health_emoji,
            "ok": ok,
            "warn": warn,
            "error": error,
            "checks": [c.to_dict() for c in all_checks],
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    print(f"\n🐍 Engram Health Check")
    print(f"{'═' * 50}")

    sections = {
        "Structure": check_structure,
        "Knowledge Freshness": check_knowledge_freshness,
        "Components": check_components,
        "Consistency": check_consistency,
    }

    # Re-run per section for display grouping
    for section_name, checker in sections.items():
        section_checks = checker(project_dir)
        print(f"\n  📂 {section_name}")
        for c in section_checks:
            print(str(c))

    print(f"\n{'═' * 50}")
    print(f"  {health_emoji} Health Score: {score}%")
    print(f"  ✅ {ok} ok  |  ⚠️  {warn} warnings  |  ❌ {error} errors")

    if error > 0:
        print(f"\n  🔧 Run the following to fix critical issues:")
        for c in all_checks:
            if c.status == "error" and c.fix:
                print(f"     • {c.fix}")

    if warn > 0 and error == 0:
        print(f"\n  💡 Suggestions:")
        for c in all_checks:
            if c.status == "warn" and c.fix:
                print(f"     • {c.fix}")

    print()


def main():
    parser = argparse.ArgumentParser(description="Engram Doctor — Health Check")
    parser.add_argument("--project-dir", default=".", help="Project root directory")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--fix", action="store_true", help="Auto-fix simple issues")
    args = parser.parse_args()

    run_doctor(args.project_dir, args.json, args.fix)


if __name__ == "__main__":
    main()
