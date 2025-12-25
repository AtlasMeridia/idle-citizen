#!/usr/bin/env python3
"""
Extract metrics from Idle Citizen session logs and git history for dashboard display.
Outputs JSON suitable for consumption by dashboard.html
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
import subprocess

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
LOGS_DIR = PROJECT_ROOT / "app support" / "logs"
ACTIVITY_DIR = PROJECT_ROOT / "activity"


def parse_meta_log(log_file):
    """Extract session metadata from a meta.log file."""
    with open(log_file, 'r') as f:
        content = f.read()

    # Extract timestamp from filename: YYYY-MM-DD_HH-MM-SS
    filename = log_file.name
    timestamp_str = filename.replace('_meta.log', '')

    # Parse start and end times
    start_match = re.search(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] Starting', content)
    end_match = re.search(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] Session complete', content)

    if not start_match or not end_match:
        return None

    start_time = datetime.strptime(start_match.group(1), '%Y-%m-%d %H:%M:%S')
    end_time = datetime.strptime(end_match.group(1), '%Y-%m-%d %H:%M:%S')
    duration_seconds = (end_time - start_time).total_seconds()

    # Extract interaction count
    interaction_match = re.search(r'interaction count: (\d+)', content)
    interactions = int(interaction_match.group(1)) if interaction_match else 0

    return {
        'timestamp': start_time.isoformat(),
        'date': start_time.strftime('%Y-%m-%d'),
        'duration_seconds': duration_seconds,
        'duration_minutes': round(duration_seconds / 60, 1),
        'interactions': interactions
    }


def get_recent_sessions(days=14):
    """Get session data from the last N days."""
    sessions = []

    if not LOGS_DIR.exists():
        return sessions

    for log_file in LOGS_DIR.glob("*_meta.log"):
        session_data = parse_meta_log(log_file)
        if session_data:
            sessions.append(session_data)

    # Sort by timestamp
    sessions.sort(key=lambda x: x['timestamp'])

    # Filter to recent days
    if sessions:
        cutoff = datetime.fromisoformat(sessions[-1]['timestamp'])
        from datetime import timedelta
        cutoff = cutoff - timedelta(days=days)
        sessions = [s for s in sessions if datetime.fromisoformat(s['timestamp']) >= cutoff]

    return sessions


def get_git_commits(days=14):
    """Get git commits from the last N days."""
    try:
        result = subprocess.run(
            ['git', 'log', f'--since={days} days ago', '--pretty=format:%H|%ai|%s'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )

        commits = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            sha, date, message = line.split('|', 2)
            commits.append({
                'sha': sha[:7],
                'date': date.split()[0],
                'message': message
            })

        return commits
    except Exception as e:
        print(f"Error getting git commits: {e}")
        return []


def count_artifacts():
    """Count artifacts created in each activity folder."""
    artifacts = {}

    for activity_dir in ACTIVITY_DIR.iterdir():
        if not activity_dir.is_dir():
            continue

        activity_name = activity_dir.name
        # Count markdown files excluding READMEs
        files = list(activity_dir.glob("**/*.md"))
        files = [f for f in files if f.name.lower() != 'readme.md']
        artifacts[activity_name] = len(files)

    return artifacts


def get_recent_artifacts(limit=10):
    """Get list of recent artifacts with metadata, sorted by modification time."""
    artifacts = []

    for activity_dir in ACTIVITY_DIR.iterdir():
        if not activity_dir.is_dir():
            continue

        activity_name = activity_dir.name

        # Get markdown files excluding READMEs
        for filepath in activity_dir.glob("**/*.md"):
            if filepath.name.lower() == 'readme.md':
                continue

            stat = filepath.stat()
            mtime = datetime.fromtimestamp(stat.st_mtime)

            # Get title from frontmatter or first heading if available
            title = filepath.stem  # Default to filename without extension
            try:
                with open(filepath, 'r') as f:
                    content = f.read(500)  # Read first 500 chars for title extraction
                    # Try YAML frontmatter first
                    frontmatter_match = re.search(r'^---\s*\ntitle:\s*(.+?)\n', content)
                    if frontmatter_match:
                        title = frontmatter_match.group(1).strip().strip('"\'')
                    else:
                        # Try first markdown heading
                        heading_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
                        if heading_match:
                            title = heading_match.group(1).strip()
            except Exception:
                pass  # Keep default title

            artifacts.append({
                'title': title,
                'filename': filepath.name,
                'activity': activity_name,
                'path': str(filepath.relative_to(PROJECT_ROOT)),
                'modified': mtime.isoformat(),
                'date': mtime.strftime('%Y-%m-%d')
            })

    # Sort by modification time, newest first
    artifacts.sort(key=lambda x: x['modified'], reverse=True)

    return artifacts[:limit]


def get_issue_stats():
    """Get issue tracker statistics."""
    issues_dir = ACTIVITY_DIR / "issues"

    open_issues = list((issues_dir / "open").glob("*.md")) if (issues_dir / "open").exists() else []
    closed_issues = list((issues_dir / "closed").glob("*.md")) if (issues_dir / "closed").exists() else []

    return {
        'open': len(open_issues),
        'closed': len(closed_issues),
        'total': len(open_issues) + len(closed_issues)
    }


def calculate_quota_usage(sessions):
    """Calculate quota usage statistics."""
    total_minutes = sum(s['duration_minutes'] for s in sessions)

    # Max plan quota: roughly 200k tokens per day, ~60 min per session
    # Let's estimate 1 hour per session * 7 days = 420 min/week budget
    weekly_budget = 420  # minutes

    return {
        'total_minutes': round(total_minutes, 1),
        'total_hours': round(total_minutes / 60, 1),
        'weekly_budget': weekly_budget,
        'utilization_percent': round((total_minutes / weekly_budget) * 100, 1) if weekly_budget > 0 else 0
    }


def main():
    """Generate dashboard metrics JSON."""
    sessions = get_recent_sessions(days=14)
    commits = get_git_commits(days=14)
    artifacts = count_artifacts()
    recent_artifacts = get_recent_artifacts(limit=10)
    issues = get_issue_stats()
    quota = calculate_quota_usage(sessions)

    # Group sessions by date
    sessions_by_date = {}
    for s in sessions:
        date = s['date']
        if date not in sessions_by_date:
            sessions_by_date[date] = []
        sessions_by_date[date].append(s)

    # Calculate daily totals
    daily_stats = []
    for date in sorted(sessions_by_date.keys()):
        day_sessions = sessions_by_date[date]
        daily_stats.append({
            'date': date,
            'session_count': len(day_sessions),
            'total_minutes': round(sum(s['duration_minutes'] for s in day_sessions), 1),
            'total_interactions': sum(s['interactions'] for s in day_sessions)
        })

    output = {
        'generated_at': datetime.now().isoformat(),
        'sessions': sessions,
        'daily_stats': daily_stats,
        'commits': commits,
        'artifacts_by_activity': artifacts,
        'recent_artifacts': recent_artifacts,
        'issues': issues,
        'quota': quota,
        'summary': {
            'total_sessions': len(sessions),
            'total_commits': len(commits),
            'total_artifacts': sum(artifacts.values())
        }
    }

    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
