#!/usr/bin/env python3
"""
Engram Genesis — Component Validator
Validates skills, agents, commands against their schemas.

Usage:
    python3 validate.py --type skill --path .claude/skills/my-skill/
    python3 validate.py --type agent --path .claude/agents/my-agent.md
    python3 validate.py --type command --path .claude/commands/my-command.md
    python3 validate.py --type manifest --path .claude/manifest.json
"""

import argparse
import json
import os
import re
import sys
import stat


class ValidationError:
    def __init__(self, level: str, message: str):
        self.level = level  # "error" | "warning"
        self.message = message

    def __str__(self):
        icon = "❌" if self.level == "error" else "⚠️"
        return f"  {icon} {self.message}"


def parse_frontmatter(content: str) -> tuple[dict | None, str]:
    """Extract YAML frontmatter from markdown content."""
    if not content.startswith("---"):
        return None, content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return None, content
    fm_text = parts[1].strip()
    body = parts[2].strip()
    fm = {}
    for line in fm_text.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if val.startswith("[") or val == "":
                # Handle list values
                if val == "" or val == "[]":
                    fm[key] = []
                else:
                    fm[key] = [v.strip().strip('"').strip("'") for v in val.strip("[]").split(",")]
            else:
                fm[key] = val
        elif line.startswith("- ") and fm:
            # Continuation of a list
            last_key = list(fm.keys())[-1]
            if isinstance(fm[last_key], list):
                fm[last_key].append(line[2:].strip().strip('"').strip("'"))
            elif fm[last_key] == "":
                fm[last_key] = [line[2:].strip().strip('"').strip("'")]
    return fm, body


def validate_skill(path: str) -> list[ValidationError]:
    """Validate a skill directory against skill.schema.md rules."""
    errors = []
    path = path.rstrip("/")
    skill_name = os.path.basename(path)

    # Rule 1: SKILL.md must exist
    skill_md = os.path.join(path, "SKILL.md")
    if not os.path.isfile(skill_md):
        errors.append(ValidationError("error", f"SKILL.md not found in {path}"))
        return errors

    with open(skill_md, "r") as f:
        content = f.read()

    # Rule 2: Valid YAML frontmatter with name + description
    fm, body = parse_frontmatter(content)
    if fm is None:
        errors.append(ValidationError("error", "Missing YAML frontmatter (must start with ---)"))
        return errors

    if "name" not in fm:
        errors.append(ValidationError("error", "Frontmatter missing required field: name"))
    if "description" not in fm:
        errors.append(ValidationError("error", "Frontmatter missing required field: description"))

    # Rule 3: name must be kebab-case and match directory
    if "name" in fm:
        name = fm["name"]
        if not re.match(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$", name):
            errors.append(ValidationError("error", f"name '{name}' is not kebab-case"))
        if name != skill_name:
            errors.append(ValidationError("warning", f"name '{name}' doesn't match directory '{skill_name}'"))

    # Rule 4: description length
    if "description" in fm:
        desc = fm["description"]
        if len(desc) < 50:
            errors.append(ValidationError("warning", f"description too short ({len(desc)} chars, min 50)"))
        if len(desc) > 500:
            errors.append(ValidationError("error", f"description too long ({len(desc)} chars, max 500)"))

    # Rule 5: Body line count
    body_lines = body.split("\n")
    if len(body_lines) > 500:
        errors.append(ValidationError("warning", f"Body has {len(body_lines)} lines (max 500 recommended)"))

    # Rule 6: Script references must point to existing files
    scripts_dir = os.path.join(path, "scripts")
    if os.path.isdir(scripts_dir):
        for script in os.listdir(scripts_dir):
            script_path = os.path.join(scripts_dir, script)
            if os.path.isfile(script_path):
                # Rule 7: Scripts must be executable with shebang
                with open(script_path, "r") as f:
                    first_line = f.readline().strip()
                if not first_line.startswith("#!"):
                    errors.append(ValidationError("warning", f"scripts/{script} missing shebang line"))
                if not os.access(script_path, os.X_OK):
                    errors.append(ValidationError("warning", f"scripts/{script} is not executable"))

    # Rule 8: composes references must be noted (can't validate existence here)
    if "composes" in fm and isinstance(fm["composes"], list):
        for composed in fm["composes"]:
            if not re.match(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$", composed):
                errors.append(ValidationError("error", f"composes: '{composed}' is not a valid skill name"))

    # Rule 9: No extraneous files
    banned_files = ["README.md", "CHANGELOG.md", "INSTALLATION.md", "INSTALL.md", "QUICK_REFERENCE.md"]
    for f in os.listdir(path):
        if f in banned_files:
            errors.append(ValidationError("warning", f"Extraneous file '{f}' — remove it"))

    return errors


def validate_agent(path: str) -> list[ValidationError]:
    """Validate an agent .md file against agent.schema.md rules."""
    errors = []

    if not os.path.isfile(path):
        errors.append(ValidationError("error", f"Agent file not found: {path}"))
        return errors

    if not path.endswith(".md"):
        errors.append(ValidationError("error", "Agent must be a .md file"))

    agent_name = os.path.basename(path).replace(".md", "")

    with open(path, "r") as f:
        content = f.read()

    fm, body = parse_frontmatter(content)
    if fm is None:
        errors.append(ValidationError("error", "Missing YAML frontmatter"))
        return errors

    # Required fields
    for field in ["name", "description", "tools"]:
        if field not in fm:
            errors.append(ValidationError("error", f"Frontmatter missing required field: {field}"))

    # Name check
    if "name" in fm:
        name = fm["name"]
        if not re.match(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$", name):
            errors.append(ValidationError("error", f"name '{name}' is not kebab-case"))
        if name != agent_name:
            errors.append(ValidationError("warning", f"name '{name}' doesn't match filename '{agent_name}'"))

    # Description length
    if "description" in fm:
        desc = fm["description"]
        if len(desc) < 50:
            errors.append(ValidationError("warning", f"description too short ({len(desc)} chars, min 50)"))

    # Body must contain rules section
    if "regra" not in body.lower() and "rule" not in body.lower():
        errors.append(ValidationError("warning", "Body should contain a 'Regras' or 'Rules' section"))

    # Line count
    if len(body.split("\n")) > 300:
        errors.append(ValidationError("warning", f"Body exceeds 300 lines"))

    return errors


def validate_command(path: str) -> list[ValidationError]:
    """Validate a command .md file against command.schema.md rules."""
    errors = []

    if not os.path.isfile(path):
        errors.append(ValidationError("error", f"Command file not found: {path}"))
        return errors

    with open(path, "r") as f:
        content = f.read()

    # Commands should NOT have frontmatter
    if content.startswith("---"):
        errors.append(ValidationError("warning", "Commands should not have YAML frontmatter"))

    # Must have actionable content
    if len(content.strip()) < 20:
        errors.append(ValidationError("error", "Command content too short — must contain executable instructions"))

    # Line count
    if len(content.split("\n")) > 200:
        errors.append(ValidationError("warning", "Command exceeds 200 lines"))

    return errors


def validate_manifest(path: str) -> list[ValidationError]:
    """Validate manifest.json structure."""
    errors = []

    if not os.path.isfile(path):
        errors.append(ValidationError("error", f"Manifest not found: {path}"))
        return errors

    try:
        with open(path, "r") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        errors.append(ValidationError("error", f"Invalid JSON: {e}"))
        return errors

    if "version" not in data and "engram_version" not in data:
        errors.append(ValidationError("error", "Missing 'version' or 'engram_version' field"))
    if "components" not in data:
        errors.append(ValidationError("error", "Missing 'components' field"))

    return errors


def main():
    parser = argparse.ArgumentParser(description="Engram Component Validator")
    parser.add_argument("--type", required=True, choices=["skill", "agent", "command", "manifest"])
    parser.add_argument("--path", required=True, help="Path to component")
    args = parser.parse_args()

    validators = {
        "skill": validate_skill,
        "agent": validate_agent,
        "command": validate_command,
        "manifest": validate_manifest,
    }

    errors = validators[args.type](args.path)

    has_errors = any(e.level == "error" for e in errors)
    has_warnings = any(e.level == "warning" for e in errors)

    if not errors:
        print(f"✅ {args.type} '{args.path}' is valid")
        sys.exit(0)
    else:
        status = "INVALID" if has_errors else "VALID (with warnings)"
        icon = "❌" if has_errors else "⚠️"
        print(f"{icon} {args.type} '{args.path}': {status}")
        for e in errors:
            print(str(e))
        sys.exit(1 if has_errors else 0)


if __name__ == "__main__":
    main()
