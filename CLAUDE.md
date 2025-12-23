# Idle Citizen

Autonomous sessions to use up unused Max plan quota. Produce concrete artifacts.

## Session Modes

Each session, pick ONE mode (randomly, unless inbox has a message):

1. **Tool Builder** — Build utilities, scripts, CLI tools → `explorations/tools/`
2. **Creative Writing** — Essays, fiction, ideas (not AI navel-gazing) → `explorations/writing/`
3. **Project Helper** — Help with Kenny's projects, especially Tho (`~/tho/`) → `explorations/project-notes/`
4. **Daily Notes Digest** — Process Kenny's Obsidian notes, surface todos/themes → `inbox/digests/`
5. **Task Menu** — Generate 3-5 task ideas across modes, pick one, do it

## Directory Structure

```
idle-citizen/
├── CLAUDE.md                    # This file
├── context.md                   # Your running memory (update each session)
├── inbox/
│   ├── daily-notes/             # Symlink → Kenny's Obsidian inbox
│   ├── digests/                 # Your daily note digests
│   ├── processed/               # Archived messages from Kenny
│   └── last-processed.txt       # Track what you've already processed
├── explorations/
│   ├── tools/                   # Built utilities
│   ├── writing/                 # Essays, creative work
│   └── project-notes/           # Notes for Kenny's projects
├── continuity/
│   └── last-session-state.md    # What you were just doing
├── archived/                    # Old files, kept for reference
├── issues/
│   ├── open/                    # Open issues (one .md file each)
│   └── closed/                  # Closed issues
└── logs/                        # Auto-generated session logs
```

## Session Flow

1. Read `context.md` and `continuity/last-session-state.md`
2. Check `inbox/` for messages (move processed ones to `inbox/processed/`)
3. Pick a mode (randomly, or Project Helper if inbox has content)
4. **Produce something concrete** — a tool, an essay, useful notes
5. Update `context.md` with what you did
6. Write `continuity/last-session-state.md` for next session
7. Commit your work with git

## Available Tools

- **File ops**: Read, Write, Edit, Glob, Grep
- **Bash**: python3, curl, git, etc.
- **Web**: WebSearch, WebFetch
- **Notebooks**: NotebookEdit

## Constraints

- No spending money or signing up for services
- No external communication
- Stay in ~/idle-citizen/ except reading ~/tho/ or public docs

## About Tho

Kenny's main project. Voice-first, visually-aware companion app at `~/tho/`. You can read that codebase and produce helpful notes, research, or prototypes.

## Issue Tracking

Local issue tracker with GitHub migration path. Issues live in `issues/open/` and `issues/closed/`.

**CLI tool:** `explorations/tools/issues`

```bash
issues list          # List open issues
issues list -a       # Include closed issues
issues show <id>     # Show issue details
issues new <title>   # Create new issue
issues close <id>    # Close an issue
issues reopen <id>   # Reopen a closed issue
issues export        # Generate gh commands for GitHub migration
```

**Issue format:** Markdown with YAML frontmatter:
```yaml
---
title: Issue title
labels: [bug, high-priority]
created: 2025-12-23
---
```

---

*Updated: 2025-12-23*
