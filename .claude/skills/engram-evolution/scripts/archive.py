#!/usr/bin/env python3
"""
Engram Evolution — Component Archiver
Creates versioned backups before modifications.

Usage:
    python3 archive.py --type skill --name my-skill --project-dir .
    python3 archive.py --type agent --name my-agent --project-dir .
    python3 archive.py --list --project-dir .
    python3 archive.py --restore --type skill --name my-skill --version 1.0.0 --project-dir .
"""

import argparse
import json
import os
import shutil
import sys
from datetime import datetime


def get_component_path(project_dir: str, comp_type: str, name: str) -> str:
    """Get the filesystem path for a component."""
    if comp_type == "skill":
        return os.path.join(project_dir, ".claude", "skills", name)
    elif comp_type == "agent":
        return os.path.join(project_dir, ".claude", "agents", f"{name}.md")
    elif comp_type == "command":
        return os.path.join(project_dir, ".claude", "commands", f"{name}.md")
    return ""


def get_version(project_dir: str, comp_type: str, name: str) -> str:
    """Get current version from manifest."""
    manifest_path = os.path.join(project_dir, ".claude", "manifest.json")
    if os.path.isfile(manifest_path):
        with open(manifest_path) as f:
            manifest = json.load(f)
        type_key = comp_type + "s"
        entry = manifest.get("components", {}).get(type_key, {}).get(name, {})
        return entry.get("version", "1.0.0")
    return "1.0.0"


def archive_component(project_dir: str, comp_type: str, name: str):
    """Create a versioned backup of a component."""
    source = get_component_path(project_dir, comp_type, name)

    if not os.path.exists(source):
        print(f"❌ {comp_type} '{name}' not found at {source}")
        sys.exit(1)

    version = get_version(project_dir, comp_type, name)
    archive_dir = os.path.join(project_dir, ".claude", "versions", name)
    os.makedirs(archive_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    archive_name = f"v{version}_{timestamp}"

    if os.path.isdir(source):
        dest = os.path.join(archive_dir, archive_name)
        shutil.copytree(source, dest)
    else:
        ext = os.path.splitext(source)[1]
        dest = os.path.join(archive_dir, f"{archive_name}{ext}")
        shutil.copy2(source, dest)

    # Write metadata
    meta = {
        "type": comp_type,
        "name": name,
        "version": version,
        "archived_at": datetime.now().isoformat(),
        "source_path": source,
    }
    meta_path = os.path.join(archive_dir, f"{archive_name}.meta.json")
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    print(f"📦 Archived {comp_type} '{name}' v{version} → .claude/versions/{name}/{archive_name}")
    return dest


def list_archives(project_dir: str):
    """List all archived versions."""
    versions_dir = os.path.join(project_dir, ".claude", "versions")
    if not os.path.isdir(versions_dir):
        print("ℹ️  No archived versions found.")
        return

    print("\n📦 Archived Versions")
    print("=" * 60)

    for component_name in sorted(os.listdir(versions_dir)):
        comp_dir = os.path.join(versions_dir, component_name)
        if not os.path.isdir(comp_dir):
            continue

        metas = [f for f in os.listdir(comp_dir) if f.endswith(".meta.json")]
        if not metas:
            continue

        print(f"\n  {component_name}:")
        for meta_file in sorted(metas):
            try:
                with open(os.path.join(comp_dir, meta_file)) as f:
                    meta = json.load(f)
                ver = meta.get("version", "?")
                dt = meta.get("archived_at", "?")[:10]
                print(f"    • v{ver} ({dt})")
            except (json.JSONDecodeError, KeyError):
                print(f"    • {meta_file} (corrupt metadata)")


def restore_component(project_dir: str, comp_type: str, name: str, version: str):
    """Restore a component from archive."""
    versions_dir = os.path.join(project_dir, ".claude", "versions", name)
    if not os.path.isdir(versions_dir):
        print(f"❌ No archives found for '{name}'")
        sys.exit(1)

    # Find matching version
    target = None
    for meta_file in os.listdir(versions_dir):
        if not meta_file.endswith(".meta.json"):
            continue
        with open(os.path.join(versions_dir, meta_file)) as f:
            meta = json.load(f)
        if meta.get("version") == version:
            archive_name = meta_file.replace(".meta.json", "")
            target = archive_name
            break

    if not target:
        print(f"❌ Version {version} not found for '{name}'")
        sys.exit(1)

    # Archive current before restoring
    print(f"  Backing up current version first...")
    archive_component(project_dir, comp_type, name)

    # Restore
    dest = get_component_path(project_dir, comp_type, name)
    source_path = os.path.join(versions_dir, target)

    if os.path.isdir(source_path):
        if os.path.exists(dest):
            shutil.rmtree(dest)
        shutil.copytree(source_path, dest)
    else:
        # Find the actual file (might have extension)
        for f in os.listdir(versions_dir):
            if f.startswith(target) and not f.endswith(".meta.json"):
                shutil.copy2(os.path.join(versions_dir, f), dest)
                break

    print(f"✅ Restored {comp_type} '{name}' to v{version}")


def main():
    parser = argparse.ArgumentParser(description="Engram Component Archiver")
    parser.add_argument("--type", choices=["skill", "agent", "command"])
    parser.add_argument("--name")
    parser.add_argument("--version", help="Version to restore")
    parser.add_argument("--project-dir", default=".")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--restore", action="store_true")
    args = parser.parse_args()

    if args.list:
        list_archives(args.project_dir)
    elif args.restore:
        if not all([args.type, args.name, args.version]):
            print("❌ --restore requires --type, --name, and --version")
            sys.exit(1)
        restore_component(args.project_dir, args.type, args.name, args.version)
    else:
        if not all([args.type, args.name]):
            print("❌ --type and --name are required")
            sys.exit(1)
        archive_component(args.project_dir, args.type, args.name)


if __name__ == "__main__":
    main()
