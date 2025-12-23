# Inbox

This folder connects Claude's autonomous sessions to Kenny's daily notes.

## Structure

```
inbox/
├── README.md              # This file
├── daily-notes/           # Symlink → Obsidian inbox (Kenny's daily notes)
├── digests/
│   ├── YYYY-MM-DD.md      # Current digests (recent notes)
│   └── backfill/
│       └── YYYY-MM-DD.md  # Historical digests (older notes)
├── processed/             # Messages from Kenny that Claude has read
├── last-processed.txt     # Timestamp of last note processing
└── backfill-progress.txt  # Tracks how far back we've processed
```

## Daily Notes Processing

**What it is:** Claude reads recent notes from `daily-notes/` and produces a digest.

**When it runs:** When Claude has nothing better to do in a session (low priority, idle time task).

**What Claude reads:**
- Daily journal entries
- Writing fragments
- Topic notes and captures
- Links and quotes

**What Claude produces:**
- One digest per day in `digests/YYYY-MM-DD.md`
- Digest can be appended/edited if Claude processes multiple times in a day
- Contains: surfaced todos, themes, captured links, patterns worth noting

**What Claude does NOT store:**
- Personal details from journal entries
- Private family matters
- Sensitive reflections

The digests are meant to be useful summaries, not reproductions.

## Processing Logic

1. Check `last-processed.txt` for when notes were last processed
2. Find notes modified in the last 7 days (or since last processed)
3. Read and synthesize
4. Write/update today's digest in `digests/`
5. Update `last-processed.txt`

## Backfill Processing

When recent notes have already been processed and Claude has idle time, it works backward through the archive.

**How it works:**
1. Check `backfill-progress.txt` for the oldest month already processed
2. Go one month further back
3. Process that month's notes, one digest per day → `digests/backfill/YYYY-MM-DD.md`
4. Update `backfill-progress.txt`
5. Continue until the entire archive is done

**Pacing:** One month of backlog per idle session.

**Backfill digests:** Same format as current digests, stored in `digests/backfill/`.

**Completion:** When `backfill-progress.txt` shows the earliest note date has been reached, backfill is complete.

## Messages from Kenny

Direct messages go in `inbox/` root (not in daily-notes).
After reading, Claude moves them to `processed/`.
