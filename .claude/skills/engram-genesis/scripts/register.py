#!/usr/bin/env python3
"""
Engram Genesis — Component Registry
Registers/unregisters components in manifest.json.

Usage:
    python3 register.py --type skill --name my-skill --source genesis --project-dir .
    python3 register.py --type agent --name my-agent --source seed --project-dir .
    python3 register.py --unregister --type skill --name my-skill --project-dir .
    python3 register.py --list --project-dir .
"""

import argparse
import json
import os
import sys
from datetime import datetime


MANIFEST_TEMPLATE = {
    "engram_version": "2.0.0",
    "installed_at": "",
    "last_updated": "",
    "components": {
        "skills": {},
        "agents": {},
        "commands": {},
    },
    "evolution": {
        "total_generations": 0,
        "total_evolutions": 0,
        "total_archived": 0,
    },
}


def get_manifest_path(project_dir: str) -> str:
    return os.path.join(project_dir, ".claude", "manifest.json")


def load_manifest(project_dir: str) -> dict:
    path = get_manifest_path(project_dir)
    if os.path.isfile(path):
        with open(path) as f:
            return json.load(f)
    # Initialize new manifest
    manifest = MANIFEST_TEMPLATE.copy()
    manifest["installed_at"] = datetime.now().isoformat()
    return manifest


def save_manifest(project_dir: str, manifest: dict):
    manifest["last_updated"] = datetime.now().isoformat()
    path = get_manifest_path(project_dir)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)


def register_component(project_dir: str, comp_type: str, name: str,
                       source: str = "genesis", version: str = "1.0.0"):
    manifest = load_manifest(project_dir)

    type_key = comp_type + "s"  # skill → skills
    if type_key not in manifest["components"]:
        manifest["components"][type_key] = {}

    now = datetime.now().isoformat()

    if name in manifest["components"][type_key]:
        # Update existing
        entry = manifest["components"][type_key][name]
        old_version = entry.get("version", "1.0.0")
        entry["version"] = version
        entry["updated_at"] = now
        entry["source"] = source
        manifest["evolution"]["total_evolutions"] += 1
        print(f"🔄 Updated {comp_type} '{name}' ({old_version} → {version})")
    else:
        # Register new
        manifest["components"][type_key][name] = {
            "version": version,
            "source": source,
            "created_at": now,
            "updated_at": now,
            "activations": 0,
            "last_used": None,
            "health": "active",
        }
        manifest["evolution"]["total_generations"] += 1
        print(f"✅ Registered {comp_type} '{name}' (v{version}, source: {source})")

    save_manifest(project_dir, manifest)


def unregister_component(project_dir: str, comp_type: str, name: str):
    manifest = load_manifest(project_dir)
    type_key = comp_type + "s"

    if type_key in manifest["components"] and name in manifest["components"][type_key]:
        manifest["components"][type_key][name]["health"] = "archived"
        manifest["evolution"]["total_archived"] += 1
        save_manifest(project_dir, manifest)
        print(f"📦 Archived {comp_type} '{name}'")
    else:
        print(f"⚠️  {comp_type} '{name}' not found in manifest")


def record_activation(project_dir: str, comp_type: str, name: str):
    """Record that a component was activated (used)."""
    manifest = load_manifest(project_dir)
    type_key = comp_type + "s"

    if type_key in manifest["components"] and name in manifest["components"][type_key]:
        entry = manifest["components"][type_key][name]
        entry["activations"] = entry.get("activations", 0) + 1
        entry["last_used"] = datetime.now().isoformat()
        save_manifest(project_dir, manifest)


def list_components(project_dir: str):
    manifest = load_manifest(project_dir)
    total = 0

    for type_key in ["skills", "agents", "commands"]:
        components = manifest.get("components", {}).get(type_key, {})
        if components:
            active = {k: v for k, v in components.items() if v.get("health") != "archived"}
            archived = {k: v for k, v in components.items() if v.get("health") == "archived"}
            print(f"\n{'='*50}")
            print(f"  {type_key.upper()} ({len(active)} active, {len(archived)} archived)")
            print(f"{'='*50}")
            for name, info in sorted(active.items()):
                acts = info.get("activations", 0)
                src = info.get("source", "?")
                ver = info.get("version", "?")
                print(f"  ✅ {name} (v{ver}) — {acts} activations — source: {src}")
                total += 1
            for name, info in sorted(archived.items()):
                print(f"  📦 {name} (archived)")

    evo = manifest.get("evolution", {})
    print(f"\n{'='*50}")
    print(f"  STATS")
    print(f"{'='*50}")
    print(f"  Total components: {total}")
    print(f"  Generations: {evo.get('total_generations', 0)}")
    print(f"  Evolutions: {evo.get('total_evolutions', 0)}")
    print(f"  Archived: {evo.get('total_archived', 0)}")


def main():
    parser = argparse.ArgumentParser(description="Engram Component Registry")
    parser.add_argument("--type", choices=["skill", "agent", "command"])
    parser.add_argument("--name", help="Component name")
    parser.add_argument("--source", default="genesis", help="Source: genesis|seed|manual|evolution|runtime")
    parser.add_argument("--version", default="1.0.0")
    parser.add_argument("--project-dir", default=".")
    parser.add_argument("--unregister", action="store_true")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--activate", action="store_true", help="Record an activation")
    args = parser.parse_args()

    if args.list:
        list_components(args.project_dir)
    elif args.activate:
        if not args.type or not args.name:
            print("❌ --activate requires --type and --name")
            sys.exit(1)
        record_activation(args.project_dir, args.type, args.name)
    elif args.unregister:
        if not args.type or not args.name:
            print("❌ --unregister requires --type and --name")
            sys.exit(1)
        unregister_component(args.project_dir, args.type, args.name)
    else:
        if not args.type or not args.name:
            print("❌ --type and --name are required")
            sys.exit(1)
        register_component(args.project_dir, args.type, args.name, args.source, args.version)


if __name__ == "__main__":
    main()
