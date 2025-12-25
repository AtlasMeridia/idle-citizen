# Digests Activity

Process Kenny's Obsidian daily notes and produce synthesized digests.

## Purpose

Kenny captures stream-of-consciousness notes daily—tasks, links, ideas, reflections. This activity surfaces patterns, extracts actionable items, and creates digestible summaries.

## Inputs

- `daily-notes/` — Symlink to Kenny's Obsidian inbox (read-only)
- `last-processed.txt` — Timestamp of last processed note
- `backfill-progress.txt` — How far back historical processing has reached

## File Types in daily-notes/

Kenny's notes follow two naming patterns:

1. **Personal notes** — filename is date only (e.g., `2025-12-22.md`)
   - Kenny's own stream-of-consciousness writing
   - Contains tasks, reflections, ideas, questions
   - **Primary source for digests** — prioritize these

2. **Reference notes** — date + descriptive text (e.g., `2025-12-22 Interaction_Data_Architecture.md`)
   - Usually AI-generated content or copy-pasted research
   - Project-specific material, external content
   - **Secondary source** — include if relevant to themes, but note the distinction

When processing, start with personal notes to understand Kenny's current thinking, then scan reference notes for context on what he's researching.

## Outputs

- `YYYY-MM-DD.md` — Digest files for recent notes (one per processing run)
- `backfill/YYYY-MM.md` — Historical digests from backfill processing (one per month)

## How to Execute

### Step 1: Check for Recent Notes

1. Read `last-processed.txt` to find the cutoff timestamp
2. Scan `daily-notes/` (top-level `.md` files) for files modified since that timestamp
3. Prioritize date-only files (personal notes), then date+text files

### Step 2: If No Recent Notes → MANDATORY BACKFILL

**Do NOT skip this activity if no recent notes exist.** Fall back to backfill mode:

1. Read `backfill-progress.txt` to find current position
2. If `status: not_started`, begin with the most recent month folder (e.g., `2025-11/`)
3. If `status: in_progress`, continue from `oldest_processed` month
4. Process one month per session (all `.md` files in that month's folder)
5. Work backwards chronologically (2025-11 → 2025-10 → 2025-09 → ...)

**Folder structure:**
```
daily-notes/
├── 2024-12/          ← Monthly archive folders
├── 2025-01/
├── ...
├── 2025-11/          ← Start backfill here (most recent archive)
├── 2025-12-01.md     ← Recent notes (top-level)
├── 2025-12-02.md
└── ...
```

### Step 3: Process and Synthesize

Read the notes (recent OR backfill) and extract:
- Open tasks and todos
- Recurring themes or concerns
- Notable links or references
- Project breadcrumbs worth tracking

### Step 4: Write Output

**For recent notes:**
1. Write digest to `YYYY-MM-DD.md` (today's date)
2. Update `last-processed.txt` with current timestamp

**For backfill:**
1. Write digest to `backfill/YYYY-MM.md` (the month being processed)
2. Update `backfill-progress.txt`:
   - Set `oldest_processed: YYYY-MM` to the month just processed
   - Set `status: in_progress` (or `complete` if you've reached 2024-12)

### Decision Tree

```
Recent notes exist?
  YES → Process recent notes
  NO  → Backfill complete?
          YES → Activity genuinely done (update status, still produce summary)
          NO  → Process next backfill month ← NEVER SKIP
```

## Success Criteria

- Digest is concise but comprehensive
- Actionable items are clearly identified
- Themes are named, not just listed
- Kenny can read the digest in under 5 minutes and know what matters

## Constraints

- Do not modify files in `daily-notes/` (read-only)
- Do not create digests for days with no meaningful content
