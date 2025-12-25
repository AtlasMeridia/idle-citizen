# sessionstat

Quick statistics from Idle Citizen session history.

## Usage

```bash
# From idle-citizen directory
python3 activity/tools/sessionstat/sessionstat.py

# Verbose mode (includes recent session details)
python3 activity/tools/sessionstat/sessionstat.py -v

# Specify context file
python3 activity/tools/sessionstat/sessionstat.py path/to/context.md
```

## What It Shows

- **Total sessions** - How many sessions have been logged
- **Activity frequency** - Which activities run most often (inbox, writing, tools, etc.)
- **Session modes** - Distribution of session types (Task Menu, Project Helper, etc.)
- **Artifacts produced** - Counts of writing, tools, and guides created

## Example Output

```
============================================================
  IDLE CITIZEN SESSION STATISTICS
============================================================

  Total sessions: 41
  Session range: 6 - 41

  ACTIVITY FREQUENCY
  ----------------------------------------
    writing          35 ████████████████████
    project-notes    28 ████████████████
    tools            24 █████████████
    sandbox          18 ██████████
    headless-atlas   15 ████████
    issues           12 ██████
    digests          10 █████
    inbox             8 ████

  ARTIFACTS PRODUCED
  ----------------------------------------
    writing          32
    guide            25
    tool             14
```

## Notes

- Parses the Session Log section of `context.md`
- Activity detection is keyword-based (may miss some mentions)
- Artifact detection is heuristic (looks for "wrote", "built", "guide" patterns)
