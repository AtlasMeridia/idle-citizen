#!/usr/bin/env python3
"""
sessiondb - Build a SQLite database of Idle Citizen activity

Aggregates data from:
- Session logs (meta logs and session JSON)
- Git commits
- Artifacts (files in activity folders)
- Issues (open and closed)

Creates a queryable SQLite database at idle-citizen.db
"""

import argparse
import json
import os
import re
import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path


def get_idle_citizen_root():
    """Find the idle-citizen project root."""
    # Check common locations
    candidates = [
        Path.home() / "Projects" / "idle-citizen",
        Path.home() / "idle-citizen",
        Path.cwd(),
    ]
    for path in candidates:
        if (path / "CLAUDE.md").exists():
            return path
    raise RuntimeError("Could not find idle-citizen project root")


def create_schema(conn):
    """Create database tables."""
    conn.executescript("""
        -- Sessions from meta logs
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY,
            started_at TEXT NOT NULL,
            ended_at TEXT,
            duration_seconds INTEGER,
            log_file TEXT NOT NULL UNIQUE
        );

        -- Git commits
        CREATE TABLE IF NOT EXISTS commits (
            hash TEXT PRIMARY KEY,
            author TEXT NOT NULL,
            date TEXT NOT NULL,
            message TEXT NOT NULL,
            files_changed INTEGER,
            insertions INTEGER,
            deletions INTEGER
        );

        -- Artifacts (files created in activity folders)
        CREATE TABLE IF NOT EXISTS artifacts (
            id INTEGER PRIMARY KEY,
            path TEXT NOT NULL UNIQUE,
            activity TEXT NOT NULL,
            filename TEXT NOT NULL,
            created_at TEXT,
            modified_at TEXT NOT NULL,
            size_bytes INTEGER NOT NULL
        );

        -- Issues
        CREATE TABLE IF NOT EXISTS issues (
            id INTEGER PRIMARY KEY,
            number TEXT NOT NULL,
            title TEXT NOT NULL,
            status TEXT NOT NULL,  -- open or closed
            created TEXT,
            updated TEXT,
            labels TEXT,  -- JSON array
            path TEXT NOT NULL UNIQUE
        );

        -- Indexes
        CREATE INDEX IF NOT EXISTS idx_sessions_started ON sessions(started_at);
        CREATE INDEX IF NOT EXISTS idx_commits_date ON commits(date);
        CREATE INDEX IF NOT EXISTS idx_artifacts_activity ON artifacts(activity);
        CREATE INDEX IF NOT EXISTS idx_issues_status ON issues(status);
    """)
    conn.commit()


def parse_meta_log(log_path):
    """Parse a meta log file to extract session info."""
    lines = log_path.read_text().strip().split('\n')

    started_at = None
    ended_at = None

    for line in lines:
        # Format: [2025-12-22 19:28:24] Message
        match = re.match(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]', line)
        if match:
            timestamp = match.group(1)
            if started_at is None:
                started_at = timestamp
            ended_at = timestamp

    duration = None
    if started_at and ended_at:
        start = datetime.strptime(started_at, "%Y-%m-%d %H:%M:%S")
        end = datetime.strptime(ended_at, "%Y-%m-%d %H:%M:%S")
        duration = int((end - start).total_seconds())

    return {
        'started_at': started_at,
        'ended_at': ended_at,
        'duration_seconds': duration,
        'log_file': str(log_path.name)
    }


def import_sessions(conn, root):
    """Import session data from meta logs."""
    logs_dir = root / "app support" / "logs"
    if not logs_dir.exists():
        print("No logs directory found")
        return 0

    imported = 0
    for log_file in logs_dir.glob("*_meta.log"):
        try:
            session = parse_meta_log(log_file)
            if session['started_at']:
                conn.execute("""
                    INSERT OR REPLACE INTO sessions (started_at, ended_at, duration_seconds, log_file)
                    VALUES (?, ?, ?, ?)
                """, (session['started_at'], session['ended_at'],
                      session['duration_seconds'], session['log_file']))
                imported += 1
        except Exception as e:
            print(f"Warning: Could not parse {log_file.name}: {e}")

    conn.commit()
    return imported


def import_commits(conn, root, days=90):
    """Import git commits from the repository."""
    try:
        result = subprocess.run(
            ['git', 'log', f'--since={days} days ago', '--format=%H|%an|%ai|%s', '--numstat'],
            cwd=root,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print(f"Git error: {result.stderr}")
            return 0

        lines = result.stdout.strip().split('\n')
        current_commit = None
        imported = 0

        for line in lines:
            if '|' in line and len(line.split('|')) == 4:
                # Commit line
                if current_commit:
                    conn.execute("""
                        INSERT OR REPLACE INTO commits
                        (hash, author, date, message, files_changed, insertions, deletions)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (current_commit['hash'], current_commit['author'],
                          current_commit['date'], current_commit['message'],
                          current_commit['files'], current_commit['insertions'],
                          current_commit['deletions']))
                    imported += 1

                parts = line.split('|')
                current_commit = {
                    'hash': parts[0],
                    'author': parts[1],
                    'date': parts[2],
                    'message': parts[3],
                    'files': 0,
                    'insertions': 0,
                    'deletions': 0
                }
            elif line.strip() and current_commit:
                # Numstat line: insertions\tdeletions\tfilename
                parts = line.split('\t')
                if len(parts) >= 2:
                    try:
                        ins = int(parts[0]) if parts[0] != '-' else 0
                        dels = int(parts[1]) if parts[1] != '-' else 0
                        current_commit['files'] += 1
                        current_commit['insertions'] += ins
                        current_commit['deletions'] += dels
                    except ValueError:
                        pass

        # Don't forget the last commit
        if current_commit:
            conn.execute("""
                INSERT OR REPLACE INTO commits
                (hash, author, date, message, files_changed, insertions, deletions)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (current_commit['hash'], current_commit['author'],
                  current_commit['date'], current_commit['message'],
                  current_commit['files'], current_commit['insertions'],
                  current_commit['deletions']))
            imported += 1

        conn.commit()
        return imported
    except Exception as e:
        print(f"Error importing commits: {e}")
        return 0


def import_artifacts(conn, root):
    """Import artifact files from activity folders."""
    activity_dir = root / "activity"
    if not activity_dir.exists():
        print("No activity directory found")
        return 0

    imported = 0
    for activity_folder in activity_dir.iterdir():
        if not activity_folder.is_dir():
            continue

        activity_name = activity_folder.name

        for artifact in activity_folder.rglob("*.md"):
            # Skip README files
            if artifact.name.lower() == 'readme.md':
                continue

            stat = artifact.stat()
            rel_path = str(artifact.relative_to(root))

            # Try to get creation time (may not be available on all systems)
            created_at = None
            try:
                # macOS stores creation time
                created_at = datetime.fromtimestamp(stat.st_birthtime).isoformat()
            except AttributeError:
                pass

            modified_at = datetime.fromtimestamp(stat.st_mtime).isoformat()

            conn.execute("""
                INSERT OR REPLACE INTO artifacts
                (path, activity, filename, created_at, modified_at, size_bytes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (rel_path, activity_name, artifact.name, created_at,
                  modified_at, stat.st_size))
            imported += 1

    conn.commit()
    return imported


def parse_issue_frontmatter(content):
    """Parse YAML-like frontmatter from an issue file."""
    result = {
        'title': None,
        'labels': [],
        'created': None,
        'updated': None
    }

    lines = content.split('\n')
    in_frontmatter = False

    for line in lines:
        if line.strip() == '---':
            if in_frontmatter:
                break
            in_frontmatter = True
            continue

        if in_frontmatter:
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()

                if key == 'title':
                    result['title'] = value
                elif key == 'labels':
                    # Parse [label1, label2] format
                    if value.startswith('[') and value.endswith(']'):
                        result['labels'] = [l.strip() for l in value[1:-1].split(',')]
                elif key == 'created':
                    result['created'] = value
                elif key == 'updated':
                    result['updated'] = value

    return result


def import_issues(conn, root):
    """Import issues from the issues folder."""
    issues_dir = root / "activity" / "issues"
    if not issues_dir.exists():
        print("No issues directory found")
        return 0

    imported = 0

    for status_dir in ['open', 'closed']:
        status_path = issues_dir / status_dir
        if not status_path.exists():
            continue

        for issue_file in status_path.glob("*.md"):
            try:
                content = issue_file.read_text()
                meta = parse_issue_frontmatter(content)

                # Extract issue number from filename (e.g., 003-some-title.md)
                number_match = re.match(r'(\d+)', issue_file.stem)
                number = number_match.group(1) if number_match else issue_file.stem

                title = meta['title'] or issue_file.stem

                conn.execute("""
                    INSERT OR REPLACE INTO issues
                    (number, title, status, created, updated, labels, path)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (number, title, status_dir, meta['created'], meta['updated'],
                      json.dumps(meta['labels']), str(issue_file.relative_to(root))))
                imported += 1
            except Exception as e:
                print(f"Warning: Could not parse issue {issue_file.name}: {e}")

    conn.commit()
    return imported


def show_stats(conn):
    """Display statistics about the database."""
    print("\n=== Database Statistics ===\n")

    # Sessions
    row = conn.execute("SELECT COUNT(*), SUM(duration_seconds) FROM sessions").fetchone()
    total_sessions = row[0]
    total_seconds = row[1] or 0
    hours = total_seconds / 3600
    print(f"Sessions: {total_sessions} ({hours:.1f} hours total)")

    # Commits
    row = conn.execute("SELECT COUNT(*), SUM(insertions), SUM(deletions) FROM commits").fetchone()
    print(f"Commits: {row[0]} (+{row[1] or 0}/-{row[2] or 0} lines)")

    # Artifacts by activity
    print("\nArtifacts by activity:")
    for row in conn.execute("""
        SELECT activity, COUNT(*) as count
        FROM artifacts
        GROUP BY activity
        ORDER BY count DESC
    """):
        print(f"  {row[0]}: {row[1]}")

    # Issues
    row = conn.execute("SELECT status, COUNT(*) FROM issues GROUP BY status").fetchall()
    issue_counts = dict(row)
    print(f"\nIssues: {issue_counts.get('open', 0)} open, {issue_counts.get('closed', 0)} closed")


def main():
    parser = argparse.ArgumentParser(
        description="Build a SQLite database of Idle Citizen activity"
    )
    parser.add_argument(
        '-o', '--output',
        default='idle-citizen.db',
        help='Output database file (default: idle-citizen.db)'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=90,
        help='Days of git history to import (default: 90)'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show statistics after building'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress progress messages'
    )

    args = parser.parse_args()

    try:
        root = get_idle_citizen_root()
        if not args.quiet:
            print(f"Found idle-citizen at: {root}")

        db_path = root / args.output
        conn = sqlite3.connect(db_path)

        if not args.quiet:
            print(f"Creating database: {db_path}")

        create_schema(conn)

        # Import data
        sessions = import_sessions(conn, root)
        if not args.quiet:
            print(f"Imported {sessions} sessions")

        commits = import_commits(conn, root, days=args.days)
        if not args.quiet:
            print(f"Imported {commits} commits")

        artifacts = import_artifacts(conn, root)
        if not args.quiet:
            print(f"Imported {artifacts} artifacts")

        issues = import_issues(conn, root)
        if not args.quiet:
            print(f"Imported {issues} issues")

        if args.stats or not args.quiet:
            show_stats(conn)

        conn.close()

        if not args.quiet:
            print(f"\nDatabase ready: {db_path}")
            print("Query with: sqlite3 idle-citizen.db")

    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
