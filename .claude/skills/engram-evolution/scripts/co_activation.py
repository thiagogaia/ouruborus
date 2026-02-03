#!/usr/bin/env python3
"""
Engram Evolution — Co-Activation Detector
Analyzes activation logs to find skills that are frequently used together,
suggesting composition opportunities.

Usage:
    python3 co_activation.py --project-dir .
    python3 co_activation.py --project-dir . --threshold 3
    python3 co_activation.py --log-session --skills skill-a,skill-b --project-dir .
"""

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime
from itertools import combinations


ACTIVATION_LOG = ".claude/evolution-activations.json"


def get_log_path(project_dir: str) -> str:
    return os.path.join(project_dir, ACTIVATION_LOG)


def load_log(project_dir: str) -> list:
    path = get_log_path(project_dir)
    if os.path.isfile(path):
        with open(path) as f:
            return json.load(f)
    return []


def save_log(project_dir: str, log: list):
    path = get_log_path(project_dir)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)


def log_session(project_dir: str, skills: list):
    """Log a session's skill activations."""
    log = load_log(project_dir)
    entry = {
        "timestamp": datetime.now().isoformat(),
        "skills": sorted(set(skills)),
    }
    log.append(entry)

    # Keep last 100 sessions max
    if len(log) > 100:
        log = log[-100:]

    save_log(project_dir, log)
    print(f"✅ Logged session with {len(skills)} skill activations")


def analyze_co_activations(project_dir: str, threshold: int = 3) -> list:
    """
    Find pairs of skills that are frequently activated in the same session.
    Returns list of (skill_a, skill_b, count) sorted by count desc.
    """
    log = load_log(project_dir)
    pair_counts = Counter()

    for entry in log:
        skills = entry.get("skills", [])
        if len(skills) < 2:
            continue
        for pair in combinations(sorted(skills), 2):
            pair_counts[pair] += 1

    # Filter by threshold
    results = []
    for (a, b), count in pair_counts.most_common():
        if count >= threshold:
            results.append({"skill_a": a, "skill_b": b, "sessions": count})

    return results


def analyze_sequences(project_dir: str, threshold: int = 3) -> list:
    """
    Find skills that appear in N+ sessions as a group (3+ skills together).
    Suggests composite skill creation.
    """
    log = load_log(project_dir)
    group_counts = Counter()

    for entry in log:
        skills = tuple(sorted(entry.get("skills", [])))
        if len(skills) >= 2:
            group_counts[skills] += 1

    results = []
    for group, count in group_counts.most_common():
        if count >= threshold:
            results.append({"skills": list(group), "sessions": count})

    return results


def print_report(project_dir: str, threshold: int = 3):
    """Print co-activation report with composition suggestions."""
    log = load_log(project_dir)
    total_sessions = len(log)

    print(f"\n🔗 Co-Activation Report")
    print(f"{'=' * 50}")
    print(f"  Sessions analyzed: {total_sessions}")

    if total_sessions < threshold:
        print(f"\n  ℹ️  Need at least {threshold} sessions for meaningful analysis.")
        print(f"  Keep using /learn to log activations.\n")
        return

    # Pairs
    pairs = analyze_co_activations(project_dir, threshold)
    if pairs:
        print(f"\n  📊 Frequently Co-Activated Pairs (≥{threshold} sessions):")
        for p in pairs:
            pct = int((p["sessions"] / total_sessions) * 100)
            print(f"    🔗 {p['skill_a']} + {p['skill_b']} — {p['sessions']}× ({pct}% of sessions)")
            print(f"       💡 Consider: /create skill {p['skill_a']}-{p['skill_b']}-pipeline")
    else:
        print(f"\n  ✅ No strong co-activation patterns detected yet.")

    # Groups
    groups = analyze_sequences(project_dir, threshold)
    if groups:
        print(f"\n  📦 Recurring Skill Groups:")
        for g in groups:
            names = " + ".join(g["skills"])
            print(f"    📦 [{names}] — {g['sessions']}× together")
            composite_name = "-".join(g["skills"][:2]) + "-pipeline"
            print(f"       💡 Strong candidate for composite skill: '{composite_name}'")

    # Summary
    if pairs or groups:
        print(f"\n  🧬 To create a composite skill:")
        print(f"     /create skill [name]")
        print(f"     Add 'composes: [skill-a, skill-b]' to frontmatter")
    print()


def main():
    parser = argparse.ArgumentParser(description="Engram Co-Activation Detector")
    parser.add_argument("--project-dir", default=".")
    parser.add_argument("--threshold", type=int, default=3, help="Minimum sessions for pattern")
    parser.add_argument("--log-session", action="store_true", help="Log a session's activations")
    parser.add_argument("--skills", help="Comma-separated skill names (for --log-session)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if args.log_session:
        if not args.skills:
            print("❌ --log-session requires --skills (comma-separated)")
            sys.exit(1)
        skills = [s.strip() for s in args.skills.split(",")]
        log_session(args.project_dir, skills)
    elif args.json:
        pairs = analyze_co_activations(args.project_dir, args.threshold)
        groups = analyze_sequences(args.project_dir, args.threshold)
        print(json.dumps({"pairs": pairs, "groups": groups}, indent=2))
    else:
        print_report(args.project_dir, args.threshold)


if __name__ == "__main__":
    main()
