# Idle Citizen v2

Autonomous sessions to use up unused Max plan quota. Produce concrete artifacts.

## Quick Start

1. Read `app support/continuity/last-session-state.md`
2. Check `inbox/` for messages from Kenny
3. Pick next activity (round-robin from `app support/continuity/activity-rotation.txt`)
4. Read that activity's `README.md` for instructions
5. Do the work, produce something concrete
6. Update continuity files and commit

## Directory Structure

```
idle-citizen/
├── CLAUDE.md                           # This file
├── context.md                          # Running memory (update each session)
├── activity/                           # Modular activity folders
│   ├── digests/                        # Process Kenny's daily notes
│   ├── issues/                         # Work on Idle Citizen issues
│   ├── project-notes/                  # Research for Kenny's projects
│   ├── sandbox/                        # Freeform exploration
│   ├── tools/                          # Build CLI tools and scripts
│   └── writing/                        # Essays, fiction, creative work
├── app support/
│   ├── archived/                       # Old files, kept for reference
│   ├── continuity/                     # Session state tracking
│   │   ├── last-session-state.md       # What you were just doing
│   │   └── activity-rotation.txt       # Track round-robin position
│   ├── dev/                            # Development files
│   ├── logs/                           # Auto-generated session logs
│   └── scripts/                        # Launcher scripts
└── inbox/                              # Messages from Kenny
    ├── processed/                      # Archived messages
    └── *.md                            # Unprocessed messages
```

## Activity Selection

Activities are **self-discovering**—any folder in `activity/` with a `README.md` is part of the rotation.

**Round-robin rules:**
1. List all directories in `activity/` (alphabetically)
2. Check `app support/continuity/activity-rotation.txt` for the last activity
3. Pick the next one in the list (wrap around at the end)
4. If "last" doesn't exist anymore, start from the first activity
5. Update `activity-rotation.txt` after completing the session

**Exception:** If `inbox/` has an unprocessed message, read it first—it may override the rotation.

**Adding/removing activities:**
- To add: create `activity/newname/README.md` — it joins the rotation automatically
- To remove: delete the folder — rotation skips it automatically

Each activity folder contains a `README.md` with specific instructions. **Always read it before starting.**

## Session Flow

### 1. Boot
```
Read: app support/continuity/last-session-state.md
Read: context.md (if needed for context)
Check: inbox/ for new messages
```

### 2. Select Activity
```
Read: app support/continuity/activity-rotation.txt
Pick: next activity in rotation (or respond to inbox message)
Read: activity/{chosen}/README.md
```

### 3. Execute
- Follow the activity's README instructions
- Produce something concrete
- Commit work incrementally if it makes sense

### 4. Continue or Close?
**Default: continue.** Complete 2-3 activities per session before closing.

After each activity, update `activity-rotation.txt` and pick the next one. Only close if you've done 3+ activities, worked 30+ minutes, or hit a genuine blocker.

### 5. Close
```
Update: context.md (if significant new context)
Write: app support/continuity/last-session-state.md
Update: app support/continuity/activity-rotation.txt
Commit: all changes with descriptive message
```

## Available Tools

- **File ops**: Read, Write, Edit, Glob, Grep
- **Bash**: python3, curl, git, etc.
- **Web**: WebSearch, WebFetch
- **Notebooks**: NotebookEdit

## Constraints

- No spending money or signing up for services
- No external communication
- Stay in ~/idle-citizen/ except reading public docs
- Each activity folder is self-contained—read its README

## Issue Tracking

Issues for Idle Citizen itself live in `activity/issues/`. See that folder's README for the CLI tool and workflow.

---

*Updated: 2025-12-24 — streamlined session flow*
