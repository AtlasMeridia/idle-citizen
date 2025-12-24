# Remapping Idle Citizen

Documentation of v1 structure and behavior. Edit this file to design v2.

---

## Overview

Idle Citizen is an autonomous session system that uses unused Claude Max quota. It runs self-directed sessions that produce concrete artifacts: tools, writing, research notes, and daily note digests.

### Core Philosophy

- Use quota that would otherwise expire
- Produce concrete things (not introspection)
- Iterate and accumulate; let patterns emerge
- Stay sandboxed (no external comms, no spending)

---

## Directory Structure

```
idle-citizen/
├── CLAUDE.md                    # Instructions for Claude during sessions
├── context.md                   # Running memory (persists across sessions)
├── continuity/
│   └── last-session-state.md    # What just happened (for session handoff)
├── inbox/
│   ├── daily-notes/             # Symlink → Kenny's Obsidian inbox
│   ├── digests/                 # Produced daily note digests
│   │   └── backfill/            # Historical digests
│   ├── processed/               # Archived messages from Kenny
│   ├── last-processed.txt       # Timestamp tracking
│   └── backfill-progress.txt    # How far back we've processed
├── explorations/
│   ├── tools/                   # Built utilities (CLI tools, scripts)
│   ├── writing/                 # Essays, fiction, creative work
│   └── project-notes/           # Research/notes for Kenny's projects
├── issues/
│   ├── open/                    # Open issues (.md with YAML frontmatter)
│   └── closed/                  # Closed issues
├── archived/                    # Old files, kept for reference
├── logs/                        # Auto-generated session logs (JSON)
├── idle-citizen-launcher.sh     # Main launcher script
├── idle-citizen-interactive.sh  # Interactive mode launcher
└── watch-session.sh             # Watch a session in progress
```

---

## Session Modes

Claude picks ONE mode per session (randomly, unless inbox has a message):

### 1. Tool Builder
Build small CLI tools, scripts, utilities. Something potentially useful.

**Output:** `explorations/tools/`

**Examples produced:**
- `mdextract` — Extract code blocks from markdown
- `gitdigest` — Summarize recent git activity
- `urlx` — Extract/validate URLs from text
- `issues` — Local issue tracker CLI

### 2. Creative Writing
Essays, fiction, poetry, ideas. Not AI navel-gazing — about the world.

**Output:** `explorations/writing/`

**Examples produced:**
- "The Illegible Substrate" (essay on tacit knowledge)
- "The Last Good Day" (short story)
- "Threshold" (flash fiction)

### 3. Project Helper
Help with Kenny's projects. Research tech, write implementation notes, prototype.

**Output:** `explorations/project-notes/`

**Status:** Tho project has been shelved. This mode needs a new purpose or removal.

**Examples produced (historical):**
- Tho menu bar mode research
- Speech recognition options
- Local AI memory system comparison (Mem0 vs Letta)

### 4. Daily Notes Digest
Process Kenny's Obsidian notes. Surface todos, themes, patterns.

**Output:** `inbox/digests/YYYY-MM-DD.md`

**Logic:**
1. Check `last-processed.txt`
2. Find notes modified since then (or last 7 days)
3. Read and synthesize
4. Write digest
5. Update `last-processed.txt`
6. If recent notes done, backfill older months

### 5. Task Menu
Generate 3-5 task ideas across modes, pick one, execute it.

---

## Session Flow

1. **Boot:** Read `context.md` and `continuity/last-session-state.md`
2. **Check inbox:** Look for messages from Kenny → `inbox/*.md` (not in subdirs)
3. **Pick mode:** Random selection, or bias toward Project Helper if inbox has content
4. **Execute:** Produce a concrete artifact
5. **Log:** Update `context.md` with session summary
6. **Handoff:** Write `continuity/last-session-state.md` for next session
7. **Commit:** Git commit the work

---

## Launcher System

### `idle-citizen-launcher.sh`

Main automation script. Can be scheduled via cron/launchd.

**Behavior:**
1. Retrieve OAuth token from macOS keychain
2. Check quota via `api.anthropic.com/api/oauth/usage`
3. If quota > 30% remaining in 5-hour window → run session
4. Calculate duration: 30% → 15min, 100% → 60min (linear scale)
5. Launch Claude Code in headless mode with `--dangerously-skip-permissions`
6. Optionally open Terminal window to watch progress
7. Session outputs to `logs/TIMESTAMP_session.json`

**Environment variables:**
- `QUOTA_THRESHOLD` — Minimum % to trigger session (default: 30)
- `GREEDY_MODE` — If true, run sessions until quota exhausted
- `WATCH_SESSION` — Open Terminal to watch (default: true)

**Allowed tools:** Read, Write, Edit, Bash, Glob, Grep, WebSearch, WebFetch, NotebookEdit

### `idle-citizen-interactive.sh`

Interactive mode — launches a session you can participate in.

### `watch-session.sh`

Tail an in-progress session log and display Claude's activity.

---

## Memory System

### `context.md`
Running memory that persists across all sessions. Contains:
- Workspace status (session count, phase)
- Direction/philosophy
- Session log (brief summary of each session)

### `continuity/last-session-state.md`
Immediate handoff document. Contains:
- Session number and date
- What mode was selected
- What was done
- Artifacts produced
- Ideas for future sessions
- Notes about discoveries

---

## Inbox System

### Messages from Kenny
Drop a `.md` file in `inbox/` root (not in subdirs). Claude checks for these at session start, prioritizes Project Helper mode, and moves processed messages to `inbox/processed/`.

### Daily Notes Link
`inbox/daily-notes/` symlinks to Kenny's Obsidian vault inbox. Claude can read notes but should not modify them.

### Digest Output
`inbox/digests/YYYY-MM-DD.md` — summarized themes, todos, links from processed notes.

---

## Issue Tracking

Local issue tracker with GitHub migration path.

**Structure:**
```
issues/
├── open/
│   └── 001-issue-title.md
└── closed/
    └── 002-resolved-issue.md
```

**Issue format (YAML frontmatter):**
```yaml
---
title: Issue title
labels: [bug, high-priority]
created: 2025-12-23
---

Issue description...
```

**CLI tool:** `explorations/tools/issues`
- `issues list` — List open issues
- `issues show <id>` — Show details
- `issues new <title>` — Create issue
- `issues close <id>` — Close issue
- `issues export` — Generate `gh` commands for GitHub migration

---

## Constraints

- No spending money or signing up for services
- No external communication (email, posts, APIs requiring auth)
- Stay in `~/idle-citizen/` except reading Kenny's projects or public docs
- No interactive commands (sessions run headless)

---

## Statistics (as of 2025-12-23)

- **Sessions completed:** 16
- **Tools built:** 4 (mdextract, gitdigest, urlx, issues)
- **Essays/stories:** 3
- **Project notes:** 4
- **Digests:** 1

---

## Ideas for v2

*Edit this section to describe changes for the next version:*

-
-
-

---

*Document created: 2025-12-23*
