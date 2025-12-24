---
name: rotation-advance
description: Select the next activity in Idle Citizen's round-robin rotation. Use when choosing what activity to work on, picking the next task, advancing the rotation, or starting a new activity after completing one.
---

# Rotation Advance

Pick the next activity in alphabetical round-robin order.

## Steps

1. **List activities**
   ```bash
   ls -1 activity/ | grep -v '^\.' | sort
   ```
   Only directories with a README.md count.

2. **Read last activity**
   ```
   app support/continuity/activity-rotation.txt
   ```

3. **Pick next**
   - Find last activity in the sorted list
   - Select the next one alphabetically
   - If last was final in list, wrap to first
   - If last doesn't exist, start from first

4. **Read the activity's README**
   ```
   activity/{chosen}/README.md
   ```

5. **Update rotation file** after completing the activity
   ```
   app support/continuity/activity-rotation.txt
   ```
   Write just the activity name (e.g., `tools`).

## Exception

If `inbox/` has unprocessed messages, handle those first—they may override the rotation.
