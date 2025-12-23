#!/usr/bin/env python3
"""
gitdigest - Summarize recent git activity in a repository

Usage:
    gitdigest [options] [path]

Options:
    -d, --days N        Look back N days (default: 7)
    -n, --commits N     Show top N commits (default: 10)
    -a, --author NAME   Filter by author name/email
    --since DATE        Start date (YYYY-MM-DD)
    --until DATE        End date (YYYY-MM-DD)
    --json              Output as JSON
    --no-stats          Skip file change statistics
    -h, --help          Show this help message

Examples:
    gitdigest                    # Summarize last 7 days in current repo
    gitdigest -d 30              # Last 30 days
    gitdigest -a "John"          # Only John's commits
    gitdigest ~/projects/myapp   # Different repository
"""

import argparse
import json
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path


def run_git(args, cwd=None):
    """Run a git command and return output."""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        if "not a git repository" in e.stderr:
            print(f"Error: Not a git repository: {cwd or '.'}", file=sys.stderr)
            sys.exit(1)
        raise


def get_commits(path, since=None, until=None, author=None):
    """Get commit data from git log."""
    # Format: hash|author|email|date|subject
    log_format = "%H|%an|%ae|%aI|%s"
    args = ["log", f"--format={log_format}"]

    if since:
        args.append(f"--since={since}")
    if until:
        args.append(f"--until={until}")
    if author:
        args.append(f"--author={author}")

    output = run_git(args, cwd=path)
    if not output:
        return []

    commits = []
    for line in output.split("\n"):
        if not line.strip():
            continue
        parts = line.split("|", 4)
        if len(parts) == 5:
            commits.append({
                "hash": parts[0],
                "author": parts[1],
                "email": parts[2],
                "date": parts[3],
                "subject": parts[4],
            })
    return commits


def get_commit_stats(path, commit_hash):
    """Get file change stats for a commit."""
    args = ["show", "--stat", "--format=", commit_hash]
    output = run_git(args, cwd=path)

    files_changed = 0
    insertions = 0
    deletions = 0

    for line in output.split("\n"):
        line = line.strip()
        if "file changed" in line or "files changed" in line:
            parts = line.split(",")
            for part in parts:
                part = part.strip()
                if "file" in part:
                    files_changed = int(part.split()[0])
                elif "insertion" in part:
                    insertions = int(part.split()[0])
                elif "deletion" in part:
                    deletions = int(part.split()[0])

    return {
        "files_changed": files_changed,
        "insertions": insertions,
        "deletions": deletions,
    }


def get_files_changed(path, since=None, until=None, author=None):
    """Get list of all files changed in the period."""
    args = ["log", "--name-only", "--format="]

    if since:
        args.append(f"--since={since}")
    if until:
        args.append(f"--until={until}")
    if author:
        args.append(f"--author={author}")

    output = run_git(args, cwd=path)

    file_counts = defaultdict(int)
    for line in output.split("\n"):
        line = line.strip()
        if line:
            file_counts[line] += 1

    return dict(sorted(file_counts.items(), key=lambda x: -x[1]))


def get_repo_name(path):
    """Get the repository name from remote or directory."""
    try:
        remote = run_git(["remote", "get-url", "origin"], cwd=path)
        # Extract repo name from URL
        name = remote.split("/")[-1]
        if name.endswith(".git"):
            name = name[:-4]
        return name
    except:
        return Path(path).resolve().name


def get_current_branch(path):
    """Get current branch name."""
    return run_git(["branch", "--show-current"], cwd=path)


def format_date(iso_date):
    """Format ISO date to readable form."""
    dt = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
    return dt.strftime("%Y-%m-%d %H:%M")


def print_summary(data, show_stats=True, max_commits=10):
    """Print formatted summary to stdout."""
    print(f"\n{'='*60}")
    print(f"  Git Digest: {data['repo_name']}")
    print(f"  Branch: {data['branch']} | Period: {data['since']} to {data['until']}")
    print(f"{'='*60}\n")

    # Quick stats
    total_commits = data["total_commits"]
    if total_commits == 0:
        print("  No commits in this period.\n")
        return

    print(f"  Commits: {total_commits}")
    print(f"  Authors: {len(data['authors'])}")
    if show_stats:
        print(f"  Lines:   +{data['total_insertions']} / -{data['total_deletions']}")
        print(f"  Files touched: {len(data['files_changed'])}")
    print()

    # Authors
    print("  Contributors:")
    for author, count in sorted(data["authors"].items(), key=lambda x: -x[1])[:5]:
        bar = "█" * min(count, 20)
        print(f"    {author:<25} {count:>3} {bar}")
    print()

    # Recent commits
    print(f"  Recent Commits (showing {min(len(data['commits']), max_commits)}):")
    for commit in data["commits"][:max_commits]:
        date = format_date(commit["date"])[:10]
        short_hash = commit["hash"][:7]
        author = commit["author"][:15]
        subject = commit["subject"][:50]
        if len(commit["subject"]) > 50:
            subject += "..."
        print(f"    {short_hash} {date} {author:<15} {subject}")
    print()

    # Hot files
    if show_stats and data["files_changed"]:
        print("  Most Changed Files:")
        for file, count in list(data["files_changed"].items())[:8]:
            bar = "█" * min(count, 15)
            # Truncate long paths
            display_file = file
            if len(file) > 45:
                display_file = "..." + file[-42:]
            print(f"    {display_file:<45} {count:>2} {bar}")
        print()

    # Activity by day of week
    if len(data["commits"]) > 5:
        day_counts = defaultdict(int)
        for commit in data["commits"]:
            dt = datetime.fromisoformat(commit["date"].replace("Z", "+00:00"))
            day_counts[dt.strftime("%A")] += 1

        print("  Activity by Day:")
        days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for day in days_order:
            count = day_counts.get(day, 0)
            bar = "█" * min(count, 20)
            print(f"    {day:<10} {count:>3} {bar}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Summarize recent git activity",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("path", nargs="?", default=".", help="Repository path")
    parser.add_argument("-d", "--days", type=int, default=7, help="Look back N days")
    parser.add_argument("-n", "--commits", type=int, default=10, help="Show top N commits")
    parser.add_argument("-a", "--author", help="Filter by author")
    parser.add_argument("--since", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--until", help="End date (YYYY-MM-DD)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--no-stats", action="store_true", help="Skip file stats")

    args = parser.parse_args()

    path = Path(args.path).resolve()
    if not path.exists():
        print(f"Error: Path does not exist: {path}", file=sys.stderr)
        sys.exit(1)

    # Calculate date range
    if args.since:
        since = args.since
    else:
        since_date = datetime.now() - timedelta(days=args.days)
        since = since_date.strftime("%Y-%m-%d")

    until = args.until or datetime.now().strftime("%Y-%m-%d")

    # Gather data
    commits = get_commits(path, since=since, until=until, author=args.author)

    # Count authors
    authors = defaultdict(int)
    for commit in commits:
        authors[commit["author"]] += 1

    # Get aggregate stats
    total_insertions = 0
    total_deletions = 0

    if not args.no_stats and commits:
        # Only get stats for a sample to avoid slow operations
        sample_size = min(len(commits), 50)
        for commit in commits[:sample_size]:
            stats = get_commit_stats(path, commit["hash"])
            total_insertions += stats["insertions"]
            total_deletions += stats["deletions"]

        # Extrapolate if we sampled
        if sample_size < len(commits):
            ratio = len(commits) / sample_size
            total_insertions = int(total_insertions * ratio)
            total_deletions = int(total_deletions * ratio)

    # Get files changed
    files_changed = {}
    if not args.no_stats:
        files_changed = get_files_changed(path, since=since, until=until, author=args.author)

    # Build result
    data = {
        "repo_name": get_repo_name(path),
        "branch": get_current_branch(path),
        "since": since,
        "until": until,
        "total_commits": len(commits),
        "authors": dict(authors),
        "commits": commits,
        "files_changed": files_changed,
        "total_insertions": total_insertions,
        "total_deletions": total_deletions,
    }

    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print_summary(data, show_stats=not args.no_stats, max_commits=args.commits)


if __name__ == "__main__":
    main()
