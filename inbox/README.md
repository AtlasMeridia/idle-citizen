# Inbox

This folder connects Claude's autonomous sessions to Kenny's daily notes.

## Structure

```
inbox/
├── README.md           # This file
├── daily-notes/        # Symlink → Obsidian inbox (Kenny's daily notes)
├── digests/            # Claude's daily digests of processed notes
├── processed/          # Messages from Kenny that Claude has read
└── last-processed.txt  # Timestamp of last note processing
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

## Messages from Kenny

Direct messages go in `inbox/` root (not in daily-notes).
After reading, Claude moves them to `processed/`.
