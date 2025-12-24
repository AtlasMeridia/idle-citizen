# cchistory

Browse and search your Claude Code conversation history.

## What It Does

Claude Code stores all conversations in `~/.claude/projects/` as JSONL files. This tool lets you list, browse, and search through that history from the command line.

## Installation

No dependencies—just Python 3.8+.

```bash
# Make it executable
chmod +x cchistory.py

# Or run with python3
python3 cchistory.py
```

## Usage

### List projects with history

```bash
cchistory projects
```

Shows all project directories that have Claude Code conversations.

### Show recent conversations

```bash
cchistory recent           # Last 10 across all projects
cchistory recent -n 20     # Last 20
```

### List sessions for a project

```bash
cchistory sessions idle-citizen      # Partial match works
cchistory sessions daemon -n 5       # Limit to 5
```

### Show a specific conversation

```bash
cchistory show ba5d4b03              # Session ID prefix
cchistory show ba5d4b03 -p idle      # Limit to project
```

### Search conversations

```bash
cchistory search "error handling"    # Search all projects
cchistory search "websocket" -p daemon  # Search specific project
```

## Examples

```
$ cchistory recent -n 3

Recent conversations:

  ba5d4b03  2025-12-24 09:18
    Project: /Users/ellis/Projects/idle-citizen
    Begin your autonomous exploration session...

  41da0563  2025-12-24 09:14
    Project: /Users/ellis/Projects/idle-citizen
    Claude Desktop Storage Format Investigation...

  fe451333  2025-12-24 09:07
    Project: /Users/ellis/Projects/idle-citizen
    can you look through the codebase of this project...
```

```
$ cchistory search "memory"

Found 4 session(s) matching 'memory':

  dcd3a42f  (/Users/ellis/Projects/idle-citizen)
    ...Mem0 for local memory storage...

  ...
```

## Data Location

Claude Code stores conversations in:

- `~/.claude/history.jsonl` — Index of prompts (timestamps, project, session IDs)
- `~/.claude/projects/<project-path>/` — Full conversation files
  - `<uuid>.jsonl` — Main conversation threads
  - `agent-*.jsonl` — Sub-agent conversations

## Notes

- Session IDs are UUIDs; prefix matching works
- Project names in storage use `-` instead of `/`
- Search is case-insensitive
- Conversations show truncated content by default
