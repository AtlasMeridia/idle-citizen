#!/usr/bin/env python3
"""
sessionstat - Quick stats from Idle Citizen session history

Parses context.md session log entries to provide statistics on:
- Total sessions and date range
- Activity distribution (which activities run most)
- Artifact counts by type
- Session frequency trends
"""

import argparse
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


def find_context_file():
    """Find context.md in current or parent directories."""
    current = Path.cwd()
    for _ in range(5):  # Check up to 5 levels
        context = current / "context.md"
        if context.exists():
            return context
        current = current.parent
    return None


def parse_sessions(content: str) -> list[dict]:
    """Parse session entries from context.md content."""
    sessions = []

    # Pattern matches: **Session N** (mode): description
    # or just **Session N**: description
    session_pattern = re.compile(
        r'\*\*Session (\d+)\*\*\s*(?:\(([^)]+)\))?\s*:?\s*(.+?)(?=\*\*Session \d+\*\*|$)',
        re.DOTALL
    )

    for match in session_pattern.finditer(content):
        num = int(match.group(1))
        mode = match.group(2) or "unknown"
        description = match.group(3).strip()

        # Extract activities mentioned
        activities = []
        activity_names = ['inbox', 'digests', 'headless-atlas', 'issues',
                         'project-notes', 'sandbox', 'tools', 'writing']
        for act in activity_names:
            if act.lower() in description.lower():
                activities.append(act)

        # Look for artifact indicators
        artifacts = []
        if 'wrote' in description.lower() and ('story' in description.lower() or 'essay' in description.lower()):
            artifacts.append('writing')
        if 'built' in description.lower() or 'tool' in description.lower():
            artifacts.append('tool')
        if 'guide' in description.lower() or 'research' in description.lower():
            artifacts.append('guide')

        sessions.append({
            'number': num,
            'mode': mode,
            'description': description[:200],
            'activities': activities,
            'artifacts': artifacts
        })

    return sessions


def print_stats(sessions: list[dict], verbose: bool = False):
    """Print session statistics."""
    if not sessions:
        print("No sessions found in context.md")
        return

    print("=" * 60)
    print("  IDLE CITIZEN SESSION STATISTICS")
    print("=" * 60)
    print()

    # Basic stats
    print(f"  Total sessions: {len(sessions)}")
    print(f"  Session range: {sessions[0]['number']} - {sessions[-1]['number']}")
    print()

    # Activity distribution
    activity_counts = Counter()
    for s in sessions:
        for act in s['activities']:
            activity_counts[act] += 1

    if activity_counts:
        print("  ACTIVITY FREQUENCY")
        print("  " + "-" * 40)
        max_count = max(activity_counts.values())
        for act, count in activity_counts.most_common():
            bar_len = int((count / max_count) * 20)
            bar = "█" * bar_len
            print(f"    {act:<16} {count:>3} {bar}")
        print()

    # Mode distribution
    mode_counts = Counter(s['mode'] for s in sessions)
    if len(mode_counts) > 1:
        print("  SESSION MODES")
        print("  " + "-" * 40)
        for mode, count in mode_counts.most_common(5):
            print(f"    {mode:<20} {count:>3}")
        print()

    # Artifact types
    artifact_counts = Counter()
    for s in sessions:
        for art in s['artifacts']:
            artifact_counts[art] += 1

    if artifact_counts:
        print("  ARTIFACTS PRODUCED")
        print("  " + "-" * 40)
        for art, count in artifact_counts.most_common():
            print(f"    {art:<16} {count:>3}")
        print()

    # Recent sessions
    if verbose:
        print("  RECENT SESSIONS")
        print("  " + "-" * 40)
        for s in sessions[-5:]:
            desc = s['description'][:60] + "..." if len(s['description']) > 60 else s['description']
            desc = desc.replace('\n', ' ')
            print(f"    Session {s['number']}: {desc}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Quick stats from Idle Citizen session history",
        epilog="""
sessionstat - Analyze Idle Citizen session patterns

Parses the session log from context.md and displays:
- Total sessions and range
- Activity frequency (which activities run most often)
- Session modes distribution
- Artifact production counts

Usage:
    sessionstat              # Quick stats
    sessionstat -v           # Include recent session details
    sessionstat path/to/context.md  # Use specific file
        """
    )
    parser.add_argument('file', nargs='?', help='Path to context.md (auto-detected if not specified)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Show recent session details')

    args = parser.parse_args()

    # Find context file
    if args.file:
        context_path = Path(args.file)
    else:
        context_path = find_context_file()

    if not context_path or not context_path.exists():
        print("Error: Could not find context.md", file=sys.stderr)
        print("Run from the idle-citizen directory or specify path", file=sys.stderr)
        sys.exit(1)

    content = context_path.read_text()
    sessions = parse_sessions(content)
    print_stats(sessions, args.verbose)


if __name__ == "__main__":
    main()
