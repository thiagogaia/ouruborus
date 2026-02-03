#!/usr/bin/env python3
"""
Engram Evolution — Usage Tracker
Reports on component health, stale components, and co-activation patterns.

Usage:
    python3 track_usage.py --project-dir . --report health
    python3 track_usage.py --project-dir . --report stale
    python3 track_usage.py --project-dir . --report summary
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta


def load_manifest(project_dir: str) -> dict:
    path = os.path.join(project_dir, ".claude", "manifest.json")
    if not os.path.isfile(path):
        print("❌ manifest.json not found. Run /init-engram first.")
        sys.exit(1)
    with open(path) as f:
        return json.load(f)


def get_all_components(manifest: dict) -> list[tuple[str, str, dict]]:
    """Return list of (type, name, info) for all components."""
    result = []
    for type_key in ["skills", "agents", "commands"]:
        components = manifest.get("components", {}).get(type_key, {})
        for name, info in components.items():
            result.append((type_key[:-1], name, info))  # "skills" → "skill"
    return result


def report_health(manifest: dict):
    """Full health report of all components."""
    components = get_all_components(manifest)
    now = datetime.now()

    print("\n🐍 Engram Health Report")
    print("=" * 60)

    active = 0
    stale = 0
    archived = 0

    for comp_type, name, info in sorted(components, key=lambda x: x[0]):
        health = info.get("health", "active")
        acts = info.get("activations", 0)
        last = info.get("last_used")
        ver = info.get("version", "?")

        if health == "archived":
            icon = "📦"
            archived += 1
        elif acts == 0:
            icon = "⚪"
            stale += 1
        elif last:
            try:
                last_dt = datetime.fromisoformat(last)
                days_ago = (now - last_dt).days
                if days_ago > 14:
                    icon = "🟡"
                    stale += 1
                else:
                    icon = "🟢"
                    active += 1
            except (ValueError, TypeError):
                icon = "🟡"
                active += 1
        else:
            icon = "🟢"
            active += 1

        last_str = ""
        if last:
            try:
                last_dt = datetime.fromisoformat(last)
                days = (now - last_dt).days
                last_str = f" (last: {days}d ago)" if days > 0 else " (last: today)"
            except (ValueError, TypeError):
                pass

        print(f"  {icon} [{comp_type:7s}] {name:30s} v{ver:6s} {acts:3d} uses{last_str}")

    total = active + stale + archived
    pct = (active / max(total - archived, 1)) * 100

    print(f"\n  {'─' * 56}")
    print(f"  🟢 Active: {active}  🟡 Stale: {stale}  📦 Archived: {archived}")
    print(f"  Health score: {pct:.0f}%")

    evo = manifest.get("evolution", {})
    print(f"\n  Generations: {evo.get('total_generations', 0)} | "
          f"Evolutions: {evo.get('total_evolutions', 0)} | "
          f"Archived: {evo.get('total_archived', 0)}")


def report_stale(manifest: dict, threshold_days: int = 14):
    """List components that haven't been used recently."""
    components = get_all_components(manifest)
    now = datetime.now()
    stale = []

    for comp_type, name, info in components:
        if info.get("health") == "archived":
            continue

        acts = info.get("activations", 0)
        last = info.get("last_used")

        is_stale = False
        reason = ""

        if acts == 0:
            is_stale = True
            reason = "never used"
        elif last:
            try:
                days = (now - datetime.fromisoformat(last)).days
                if days > threshold_days:
                    is_stale = True
                    reason = f"not used in {days} days"
            except (ValueError, TypeError):
                pass

        if is_stale:
            stale.append((comp_type, name, reason, info))

    if not stale:
        print("✅ No stale components found.")
        return

    print(f"\n⚠️  Stale Components ({len(stale)} found)")
    print("=" * 60)
    for comp_type, name, reason, info in stale:
        src = info.get("source", "?")
        print(f"  🟡 [{comp_type:7s}] {name:30s} — {reason} (source: {src})")

    print(f"\n  💡 Actions:")
    print(f"     • Archive if no longer needed")
    print(f"     • Merge into another skill if overlapping")
    print(f"     • Update description if triggers are wrong")


def report_summary(manifest: dict):
    """Quick summary for /learn integration."""
    components = get_all_components(manifest)
    active = [c for c in components if c[2].get("health") != "archived"]
    by_acts = sorted(active, key=lambda x: x[2].get("activations", 0), reverse=True)

    print("\n📊 Component Usage Summary")
    print("─" * 40)

    if by_acts:
        top = by_acts[:5]
        print("  Top used:")
        for _, name, info in top:
            print(f"    {info.get('activations', 0):3d}× {name}")

        bottom = [c for c in by_acts if c[2].get("activations", 0) == 0]
        if bottom:
            print(f"\n  Never used ({len(bottom)}):")
            for _, name, _ in bottom[:5]:
                print(f"    ⚪ {name}")

    evo = manifest.get("evolution", {})
    print(f"\n  Total: {len(active)} active | "
          f"{evo.get('total_generations', 0)} generated | "
          f"{evo.get('total_evolutions', 0)} evolved")

    # Highlight runtime components
    runtime = [c for c in active if c[2].get("source") == "runtime"]
    if runtime:
        print(f"\n  ⚡ Runtime-created ({len(runtime)}):")
        for _, name, info in runtime:
            acts = info.get("activations", 0)
            print(f"    ⚡ {name} — {acts} uses (evaluate: keep or archive?)")


def main():
    parser = argparse.ArgumentParser(description="Engram Usage Tracker")
    parser.add_argument("--project-dir", default=".")
    parser.add_argument("--report", choices=["health", "stale", "summary"], default="health")
    parser.add_argument("--threshold", type=int, default=14, help="Days for stale threshold")
    args = parser.parse_args()

    manifest = load_manifest(args.project_dir)

    if args.report == "health":
        report_health(manifest)
    elif args.report == "stale":
        report_stale(manifest, args.threshold)
    elif args.report == "summary":
        report_summary(manifest)


if __name__ == "__main__":
    main()
