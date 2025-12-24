---
name: session-close
description: End an Idle Citizen session properly. Use when finishing work, ending the session, closing out, wrapping up, or when the session timeout is approaching. Ensures continuity files are updated and changes are committed.
---

# Session Close

Checklist for ending an Idle Citizen session cleanly.

## Steps

1. **Update context.md** (only if significant new context emerged)
   - New discoveries about Kenny's projects or preferences
   - Patterns worth remembering
   - Skip if nothing notable

2. **Write last-session-state.md**
   ```
   app support/continuity/last-session-state.md
   ```
   Include:
   - What activity was in progress
   - What was accomplished
   - Any blockers or notes for next session

3. **Verify activity-rotation.txt** is current
   ```
   app support/continuity/activity-rotation.txt
   ```
   Should reflect the last completed activity.

4. **Commit all changes**
   ```bash
   git add -A && git commit -m "Session: [brief description of work]"
   ```

## Skip Conditions

- If no work was done, skip the commit
- If session was interrupted mid-task, note the interruption in last-session-state.md
