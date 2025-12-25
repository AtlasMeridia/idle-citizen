#!/usr/bin/env python3
"""
artifacts - Analyze and report on Idle Citizen artifacts

Scans activity folders, extracts metadata, and generates reports
on what's been produced across sessions.
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


def get_activity_root() -> Path:
    """Get the activity folder path."""
    # Default to idle-citizen in home directory
    idle_citizen = Path.home() / "Projects" / "idle-citizen"
    if idle_citizen.exists():
        return idle_citizen / "activity"
    # Fall back to current directory's parent
    return Path.cwd().parent


def extract_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from markdown content."""
    frontmatter = {}
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            for line in parts[1].strip().split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    frontmatter[key.strip()] = value.strip()
    return frontmatter


def extract_title(content: str) -> str:
    """Extract title from markdown (first H1 or first line)."""
    lines = content.strip().split("\n")
    for line in lines:
        if line.startswith("# "):
            return line[2:].strip()
        if line.startswith("---"):
            continue
        if line.strip() and not line.startswith("#"):
            # Skip frontmatter
            continue
    # Fall back to first non-empty line
    for line in lines:
        if line.strip() and not line.startswith("---"):
            return line.strip()[:50]
    return "Untitled"


def count_words(content: str) -> int:
    """Count words in content, excluding frontmatter."""
    # Remove frontmatter
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            content = parts[2]
    # Remove code blocks
    content = re.sub(r"```[\s\S]*?```", "", content)
    # Count words
    words = re.findall(r"\b\w+\b", content)
    return len(words)


def get_session_from_context() -> Optional[int]:
    """Try to extract session number from context.md."""
    context_path = get_activity_root().parent / "context.md"
    if context_path.exists():
        content = context_path.read_text()
        match = re.search(r"\*\*Sessions completed:\*\*\s*(\d+)", content)
        if match:
            return int(match.group(1))
    return None


def scan_artifact(path: Path) -> Dict[str, Any]:
    """Scan a single artifact file and extract metadata."""
    try:
        stat = path.stat()
        content = path.read_text(errors="ignore")

        artifact = {
            "path": str(path),
            "name": path.stem,
            "activity": path.parent.name,
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "size_bytes": stat.st_size,
            "word_count": count_words(content),
        }

        # Extract title
        if path.suffix == ".md":
            artifact["title"] = extract_title(content)
            artifact["frontmatter"] = extract_frontmatter(content)
        else:
            artifact["title"] = path.stem

        return artifact
    except Exception as e:
        return {"path": str(path), "error": str(e)}


def scan_activity(activity_path: Path) -> List[Dict]:
    """Scan an activity folder for artifacts."""
    artifacts = []

    # Skip certain folders
    skip_folders = {"__pycache__", ".git", "node_modules"}

    for item in activity_path.rglob("*"):
        if item.is_file():
            # Skip if in a skipped folder
            if any(skip in item.parts for skip in skip_folders):
                continue
            # Skip hidden files
            if item.name.startswith("."):
                continue
            # Skip READMEs (they're documentation, not artifacts)
            if item.name.lower() == "readme.md":
                continue

            artifact = scan_artifact(item)
            artifacts.append(artifact)

    return artifacts


def scan_all_activities(root: Path) -> Dict[str, List]:
    """Scan all activity folders."""
    activities = {}

    for item in root.iterdir():
        if item.is_dir() and not item.name.startswith("."):
            artifacts = scan_activity(item)
            if artifacts:
                activities[item.name] = artifacts

    return activities


def format_size(size_bytes: int) -> str:
    """Format byte size to human-readable."""
    for unit in ["B", "KB", "MB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}GB"


def cmd_list(args):
    """List all artifacts."""
    root = get_activity_root()
    activities = scan_all_activities(root)

    all_artifacts = []
    for activity, artifacts in activities.items():
        for artifact in artifacts:
            artifact["activity"] = activity
            all_artifacts.append(artifact)

    # Sort by modification time
    all_artifacts.sort(key=lambda x: x.get("modified", ""), reverse=True)

    if args.json:
        print(json.dumps(all_artifacts, indent=2))
        return

    # Limit if specified
    if args.limit:
        all_artifacts = all_artifacts[:args.limit]

    # Print table
    print(f"{'Activity':<15} {'Title':<40} {'Words':>7} {'Modified':<12}")
    print("-" * 80)

    for a in all_artifacts:
        title = a.get("title", a.get("name", "?"))[:38]
        words = a.get("word_count", 0)
        modified = a.get("modified", "")[:10]
        activity = a.get("activity", "?")[:13]
        print(f"{activity:<15} {title:<40} {words:>7} {modified:<12}")


def cmd_stats(args):
    """Show statistics about artifacts."""
    root = get_activity_root()
    activities = scan_all_activities(root)

    stats = {
        "total_artifacts": 0,
        "total_words": 0,
        "total_bytes": 0,
        "by_activity": {},
        "by_extension": defaultdict(int),
    }

    for activity, artifacts in activities.items():
        activity_stats = {
            "count": len(artifacts),
            "words": sum(a.get("word_count", 0) for a in artifacts),
            "bytes": sum(a.get("size_bytes", 0) for a in artifacts),
        }
        stats["by_activity"][activity] = activity_stats
        stats["total_artifacts"] += len(artifacts)
        stats["total_words"] += activity_stats["words"]
        stats["total_bytes"] += activity_stats["bytes"]

        for a in artifacts:
            ext = Path(a["path"]).suffix or ".other"
            stats["by_extension"][ext] += 1

    if args.json:
        stats["by_extension"] = dict(stats["by_extension"])
        print(json.dumps(stats, indent=2))
        return

    # Get session count
    sessions = get_session_from_context()

    print("=== Idle Citizen Artifact Statistics ===\n")
    print(f"Total artifacts: {stats['total_artifacts']}")
    print(f"Total words: {stats['total_words']:,}")
    print(f"Total size: {format_size(stats['total_bytes'])}")

    if sessions:
        avg = stats['total_artifacts'] / sessions
        print(f"Sessions: {sessions} ({avg:.1f} artifacts/session)")

    print("\n--- By Activity ---")
    for activity, data in sorted(stats["by_activity"].items()):
        print(f"  {activity}: {data['count']} files, {data['words']:,} words")

    print("\n--- By Extension ---")
    for ext, count in sorted(stats["by_extension"].items(), key=lambda x: -x[1]):
        print(f"  {ext}: {count}")


def cmd_recent(args):
    """Show most recently modified artifacts."""
    root = get_activity_root()
    activities = scan_all_activities(root)

    all_artifacts = []
    for activity, artifacts in activities.items():
        for artifact in artifacts:
            artifact["activity"] = activity
            all_artifacts.append(artifact)

    # Sort by modification time
    all_artifacts.sort(key=lambda x: x.get("modified", ""), reverse=True)

    limit = args.count or 10
    recent = all_artifacts[:limit]

    if args.json:
        print(json.dumps(recent, indent=2))
        return

    print(f"=== {limit} Most Recent Artifacts ===\n")

    for i, a in enumerate(recent, 1):
        title = a.get("title", a.get("name", "?"))
        activity = a.get("activity", "?")
        words = a.get("word_count", 0)
        modified = a.get("modified", "")[:10]

        print(f"{i:2}. [{activity}] {title}")
        print(f"    {words:,} words, modified {modified}")
        print()


def cmd_activity(args):
    """Show artifacts for a specific activity."""
    root = get_activity_root()
    activity_path = root / args.name

    if not activity_path.exists():
        print(f"Activity not found: {args.name}")
        print(f"Available: {', '.join(d.name for d in root.iterdir() if d.is_dir())}")
        sys.exit(1)

    artifacts = scan_activity(activity_path)

    # Sort by modification time
    artifacts.sort(key=lambda x: x.get("modified", ""), reverse=True)

    if args.json:
        print(json.dumps(artifacts, indent=2))
        return

    total_words = sum(a.get("word_count", 0) for a in artifacts)

    print(f"=== {args.name} ===")
    print(f"Files: {len(artifacts)}, Total words: {total_words:,}\n")

    for a in artifacts:
        title = a.get("title", a.get("name", "?"))
        words = a.get("word_count", 0)
        modified = a.get("modified", "")[:10]

        print(f"  {title}")
        print(f"    {words:,} words, {modified}")


def cmd_search(args):
    """Search artifacts by title or content."""
    root = get_activity_root()
    activities = scan_all_activities(root)

    query = args.query.lower()
    matches = []

    for activity, artifacts in activities.items():
        for artifact in artifacts:
            # Check title
            title = artifact.get("title", "").lower()
            name = artifact.get("name", "").lower()

            if query in title or query in name:
                artifact["match_type"] = "title"
                artifact["activity"] = activity
                matches.append(artifact)
                continue

            # Check content if requested
            if args.content:
                try:
                    content = Path(artifact["path"]).read_text(errors="ignore").lower()
                    if query in content:
                        artifact["match_type"] = "content"
                        artifact["activity"] = activity
                        matches.append(artifact)
                except:
                    pass

    if args.json:
        print(json.dumps(matches, indent=2))
        return

    if not matches:
        print(f"No matches for: {args.query}")
        return

    print(f"=== {len(matches)} matches for '{args.query}' ===\n")

    for m in matches:
        title = m.get("title", m.get("name", "?"))
        activity = m.get("activity", "?")
        match_type = m.get("match_type", "?")
        print(f"  [{activity}] {title} ({match_type} match)")


def main():
    parser = argparse.ArgumentParser(
        description="Analyze and report on Idle Citizen artifacts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  list      List all artifacts (sorted by recent)
  stats     Show statistics about artifacts
  recent    Show most recently modified artifacts
  activity  Show artifacts for a specific activity
  search    Search artifacts by title or content

Examples:
  artifacts stats
  artifacts list --limit 20
  artifacts recent --count 5
  artifacts activity writing
  artifacts search "memory" --content
""",
    )

    parser.add_argument("--json", action="store_true", help="Output as JSON")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # list command
    list_parser = subparsers.add_parser("list", help="List all artifacts")
    list_parser.add_argument("--limit", type=int, help="Limit number of results")
    list_parser.set_defaults(func=cmd_list)

    # stats command
    stats_parser = subparsers.add_parser("stats", help="Show statistics")
    stats_parser.set_defaults(func=cmd_stats)

    # recent command
    recent_parser = subparsers.add_parser("recent", help="Show recent artifacts")
    recent_parser.add_argument("--count", "-n", type=int, default=10, help="Number to show")
    recent_parser.set_defaults(func=cmd_recent)

    # activity command
    activity_parser = subparsers.add_parser("activity", help="Show activity artifacts")
    activity_parser.add_argument("name", help="Activity name (e.g., writing, sandbox)")
    activity_parser.set_defaults(func=cmd_activity)

    # search command
    search_parser = subparsers.add_parser("search", help="Search artifacts")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--content", "-c", action="store_true",
                               help="Also search content (slower)")
    search_parser.set_defaults(func=cmd_search)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
