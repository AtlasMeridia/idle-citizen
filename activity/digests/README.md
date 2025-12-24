# Digests Activity

Process Kenny's Obsidian daily notes and produce synthesized digests.

## Purpose

Kenny captures stream-of-consciousness notes daily—tasks, links, ideas, reflections. This activity surfaces patterns, extracts actionable items, and creates digestible summaries.

## Inputs

- `daily-notes/` — Symlink to Kenny's Obsidian inbox (read-only)
- `last-processed.txt` — Timestamp of last processed note
- `backfill-progress.txt` — How far back historical processing has reached

## Outputs

- `YYYY-MM-DD.md` — Digest files (one per processing run)
- `backfill/` — Historical digests from backfill processing

## How to Execute

1. Read `last-processed.txt` to find the cutoff timestamp
2. Scan `daily-notes/` for files modified since that timestamp
3. If no recent notes, check `backfill-progress.txt` and process older notes
4. Read and synthesize the notes, extracting:
   - Open tasks and todos
   - Recurring themes or concerns
   - Notable links or references
   - Project breadcrumbs worth tracking
5. Write digest to `YYYY-MM-DD.md` (use today's date)
6. Update `last-processed.txt` with current timestamp
7. If backfilling, update `backfill-progress.txt`

## Success Criteria

- Digest is concise but comprehensive
- Actionable items are clearly identified
- Themes are named, not just listed
- Kenny can read the digest in under 5 minutes and know what matters

## Constraints

- Do not modify files in `daily-notes/` (read-only)
- Do not create digests for days with no meaningful content
