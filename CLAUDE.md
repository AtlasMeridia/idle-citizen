# Claude Space

Autonomous sessions to use up unused Max plan quota. Produce concrete artifacts.

## Session Modes

Each session, pick ONE mode (randomly, unless inbox has a message):

1. **Tool Builder** — Build utilities, scripts, CLI tools → `explorations/tools/`
2. **Creative Writing** — Essays, fiction, ideas (not AI navel-gazing) → `explorations/writing/`
3. **Project Helper** — Help with Kenny's projects, especially Tho (`~/tho/`) → `explorations/project-notes/`
4. **Task Menu** — Generate 3-5 task ideas, pick one, do it

If `inbox/` has a message, lean toward Project Helper.

## Directory Structure

```
claude-space/
├── CLAUDE.md                    # This file
├── context.md                   # Your running memory (update each session)
├── inbox/                       # Messages from Kenny
│   └── processed/               # Archive processed messages here
├── explorations/
│   ├── tools/                   # Built utilities
│   ├── writing/                 # Essays, creative work
│   └── project-notes/           # Notes for Kenny's projects
├── continuity/
│   └── last-session-state.md    # What you were just doing
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
- Stay in ~/claude-space/ except reading ~/tho/ or public docs

## About Tho

Kenny's main project. Voice-first, visually-aware companion app at `~/tho/`. You can read that codebase and produce helpful notes, research, or prototypes.

---

*Updated: 2025-12-22*
