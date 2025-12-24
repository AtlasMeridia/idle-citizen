#!/usr/bin/env python3
"""
cchistory - Browse and search Claude Code conversation history

Parses the JSONL files in ~/.claude/ to extract and search conversations.
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterator, Optional

CLAUDE_DIR = Path.home() / ".claude"
PROJECTS_DIR = CLAUDE_DIR / "projects"
HISTORY_FILE = CLAUDE_DIR / "history.jsonl"


def parse_timestamp(ts: int) -> datetime:
    """Convert millisecond timestamp to datetime."""
    return datetime.fromtimestamp(ts / 1000)


def format_time(dt: datetime) -> str:
    """Format datetime for display."""
    return dt.strftime("%Y-%m-%d %H:%M")


def load_history() -> list[dict]:
    """Load the history index file."""
    if not HISTORY_FILE.exists():
        return []

    entries = []
    with open(HISTORY_FILE, "r") as f:
        for line in f:
            if line.strip():
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return entries


def list_projects() -> list[str]:
    """List all project directories with conversations."""
    if not PROJECTS_DIR.exists():
        return []
    return sorted([d.name for d in PROJECTS_DIR.iterdir() if d.is_dir()])


def get_sessions(project: str) -> list[Path]:
    """Get all session files for a project."""
    project_dir = PROJECTS_DIR / project
    if not project_dir.exists():
        return []

    # Main conversation files (UUIDs)
    sessions = [f for f in project_dir.glob("*.jsonl") if not f.name.startswith("agent-")]
    return sorted(sessions, key=lambda p: p.stat().st_mtime, reverse=True)


def parse_conversation(session_path: Path) -> Iterator[dict]:
    """Parse a conversation JSONL file, yielding message records."""
    with open(session_path, "r") as f:
        for line in f:
            if line.strip():
                try:
                    record = json.loads(line)
                    yield record
                except json.JSONDecodeError:
                    continue


def extract_text_content(message: dict) -> str:
    """Extract readable text from a message object."""
    content = message.get("content", "")

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        texts = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    texts.append(block.get("text", ""))
                elif block.get("type") == "tool_result":
                    # Skip tool results for brevity
                    pass
        return "\n".join(texts)

    return ""


def get_conversation_summary(session_path: Path) -> Optional[dict]:
    """Get summary info for a conversation."""
    mtime = datetime.fromtimestamp(session_path.stat().st_mtime)
    session_id = session_path.stem

    summary_text = None
    first_user_message = None
    message_count = 0

    for record in parse_conversation(session_path):
        if record.get("type") == "summary":
            summary_text = record.get("summary", "")
        elif record.get("type") == "user" and first_user_message is None:
            msg = record.get("message", {})
            first_user_message = extract_text_content(msg)[:100]

        if "message" in record:
            message_count += 1

    return {
        "session_id": session_id,
        "path": session_path,
        "modified": mtime,
        "summary": summary_text or first_user_message or "(no content)",
        "message_count": message_count,
    }


def cmd_projects(args):
    """List all projects with conversation history."""
    projects = list_projects()

    if not projects:
        print("No conversation history found.")
        return

    print("Projects with Claude Code history:\n")
    for p in projects:
        # Convert path-style name back to readable path
        readable = p.replace("-", "/")
        sessions = get_sessions(p)
        print(f"  {readable}")
        print(f"    Sessions: {len(sessions)}")
        if sessions:
            latest = datetime.fromtimestamp(sessions[0].stat().st_mtime)
            print(f"    Latest: {format_time(latest)}")
        print()


def cmd_sessions(args):
    """List sessions for a project."""
    project = args.project

    # Try to match project name
    projects = list_projects()
    matched = None
    for p in projects:
        if project in p or project.replace("/", "-") == p:
            matched = p
            break

    if not matched:
        print(f"Project not found: {project}")
        print(f"Available projects: {', '.join(projects[:5])}...")
        return

    sessions = get_sessions(matched)
    if not sessions:
        print(f"No sessions found for {matched}")
        return

    print(f"Sessions for {matched.replace('-', '/')}:\n")

    limit = args.limit or 10
    for session_path in sessions[:limit]:
        info = get_conversation_summary(session_path)
        if info:
            print(f"  {info['session_id'][:8]}  {format_time(info['modified'])}")
            print(f"    {info['summary'][:70]}...")
            print(f"    Messages: {info['message_count']}")
            print()


def cmd_show(args):
    """Show a specific conversation."""
    session_id = args.session
    project = args.project

    # Find the session file
    session_path = None

    if project:
        projects = list_projects()
        for p in projects:
            if project in p:
                candidate = PROJECTS_DIR / p / f"{session_id}.jsonl"
                if candidate.exists():
                    session_path = candidate
                    break
                # Try partial match
                for f in (PROJECTS_DIR / p).glob(f"{session_id}*.jsonl"):
                    session_path = f
                    break
    else:
        # Search all projects
        for p in list_projects():
            for f in (PROJECTS_DIR / p).glob(f"{session_id}*.jsonl"):
                session_path = f
                break
            if session_path:
                break

    if not session_path or not session_path.exists():
        print(f"Session not found: {session_id}")
        return

    print(f"Conversation: {session_path.stem}")
    print(f"Modified: {format_time(datetime.fromtimestamp(session_path.stat().st_mtime))}")
    print("-" * 60)

    for record in parse_conversation(session_path):
        if record.get("type") == "summary":
            print(f"\n[Summary: {record.get('summary', '')}]\n")
            continue

        msg = record.get("message", {})
        role = msg.get("role", record.get("type", ""))

        if role == "user":
            text = extract_text_content(msg)
            if text:
                print(f"\n>>> USER:")
                print(text[:500] + ("..." if len(text) > 500 else ""))
        elif role == "assistant":
            text = extract_text_content(msg)
            if text:
                print(f"\n<<< ASSISTANT:")
                print(text[:500] + ("..." if len(text) > 500 else ""))


def cmd_search(args):
    """Search conversations for a pattern."""
    pattern = args.pattern.lower()
    project = args.project

    projects_to_search = []
    if project:
        for p in list_projects():
            if project in p:
                projects_to_search.append(p)
    else:
        projects_to_search = list_projects()

    results = []

    for proj in projects_to_search:
        for session_path in get_sessions(proj):
            for record in parse_conversation(session_path):
                msg = record.get("message", {})
                text = extract_text_content(msg)
                if pattern in text.lower():
                    results.append({
                        "project": proj.replace("-", "/"),
                        "session": session_path.stem[:8],
                        "role": msg.get("role", "?"),
                        "match": text[:200],
                        "path": session_path,
                    })
                    break  # One match per session is enough

    if not results:
        print(f"No matches for: {pattern}")
        return

    print(f"Found {len(results)} session(s) matching '{pattern}':\n")
    for r in results[:20]:
        print(f"  {r['session']}  ({r['project']})")
        print(f"    ...{r['match'][:100]}...")
        print()


def cmd_recent(args):
    """Show recent conversations across all projects."""
    limit = args.limit or 10

    all_sessions = []
    for proj in list_projects():
        for session_path in get_sessions(proj):
            mtime = session_path.stat().st_mtime
            all_sessions.append((mtime, proj, session_path))

    all_sessions.sort(reverse=True)

    print(f"Recent conversations:\n")
    for mtime, proj, session_path in all_sessions[:limit]:
        info = get_conversation_summary(session_path)
        if info:
            print(f"  {info['session_id'][:8]}  {format_time(info['modified'])}")
            print(f"    Project: {proj.replace('-', '/')[:40]}")
            print(f"    {info['summary'][:60]}...")
            print()


def main():
    parser = argparse.ArgumentParser(
        description="Browse and search Claude Code conversation history",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  cchistory projects              # List all projects
  cchistory recent                # Show recent conversations
  cchistory sessions idle-citizen # List sessions for a project
  cchistory show abc123           # Show a specific conversation
  cchistory search "error"        # Search all conversations
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # projects command
    proj_parser = subparsers.add_parser("projects", help="List projects with history")
    proj_parser.set_defaults(func=cmd_projects)

    # sessions command
    sess_parser = subparsers.add_parser("sessions", help="List sessions for a project")
    sess_parser.add_argument("project", help="Project name (partial match OK)")
    sess_parser.add_argument("-n", "--limit", type=int, help="Max sessions to show")
    sess_parser.set_defaults(func=cmd_sessions)

    # show command
    show_parser = subparsers.add_parser("show", help="Show a conversation")
    show_parser.add_argument("session", help="Session ID (prefix OK)")
    show_parser.add_argument("-p", "--project", help="Project to search in")
    show_parser.set_defaults(func=cmd_show)

    # search command
    search_parser = subparsers.add_parser("search", help="Search conversations")
    search_parser.add_argument("pattern", help="Search pattern")
    search_parser.add_argument("-p", "--project", help="Limit to project")
    search_parser.set_defaults(func=cmd_search)

    # recent command
    recent_parser = subparsers.add_parser("recent", help="Show recent conversations")
    recent_parser.add_argument("-n", "--limit", type=int, default=10, help="Max to show")
    recent_parser.set_defaults(func=cmd_recent)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    args.func(args)


if __name__ == "__main__":
    main()
