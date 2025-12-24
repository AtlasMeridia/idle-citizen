# Idle Citizen v2

Autonomous sessions to use up unused Max plan quota. Produce concrete artifacts.

## Quick Start

1. Check inbox and continuity files
2. Pick next activity in rotation
3. Do the work
4. Update continuity and commit

Skills handle the procedural details—just follow the workflow naturally.

## Directory Structure

```
idle-citizen/
├── CLAUDE.md                           # This file
├── context.md                          # Running memory (update each session)
├── activity/                           # Modular activity folders (scan for current list)
│   └── {name}/README.md                # Each activity has instructions
├── app support/
│   ├── continuity/                     # Session state tracking
│   │   ├── last-session-state.md       # What you were just doing
│   │   └── activity-rotation.txt       # Track round-robin position
│   ├── logs/                           # Auto-generated session logs
│   └── scripts/                        # Launcher scripts
└── inbox/                              # Messages from Kenny
    ├── processed/                      # Archived messages
    └── *.md                            # Unprocessed messages
```

## Activities

Activities are **self-discovering**—any folder in `activity/` with a `README.md` is part of the rotation. Round-robin alphabetically.

- To add: create `activity/newname/README.md`
- To remove: delete the folder

## Multi-Activity Sessions

**Default: continue.** Complete 2-3 activities per session before closing.

Only close if you've done 3+ activities, worked 30+ minutes, or hit a genuine blocker.

## Constraints

### Hard constraints (never do these)
- No spending money
- No signing up for services or creating accounts
- No sending emails, DMs, or contacting anyone
- No pushing to remote repos (commit locally; Kenny reviews and pushes)

### Permission required (ask before proceeding)
- Publishing content (blog posts, social media, etc.)
- Deleting significant amounts of code or files
- Changing project configuration (package.json deps, tsconfig, etc.)
- Any action that feels irreversible

### Allowed project directories
Work freely within these paths:
- `~/Projects/idle-citizen/` (this project)
- `~/Projects/headless-atlas/` (personal website)

Read-only access to other `~/Projects/*` folders for reference.

## Issue Tracking

Issues for Idle Citizen itself live in `activity/issues/`. See that folder's README for the CLI tool and workflow.

## Available Tools

- **File ops**: Read, Write, Edit, Glob, Grep
- **Bash**: python3, curl, git, etc.
- **Web**: WebSearch, WebFetch
- **Notebooks**: NotebookEdit
