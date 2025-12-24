---
title: Low Quota Utilization - Session Intensity
labels: [resolved]
created: 2025-12-23
updated: 2025-12-24
---

## Problem

Individual sessions are too short. They complete one artifact and exit in 2-5 minutes, even though they have 60 minutes allocated.

## Desired Behavior

Sessions should be more substantial — tackle larger projects, chain multiple tasks, or go deeper on a single topic.

## Resolution (Session 19)

System prompt updated with explicit "Multi-Activity Sessions" section:

- [x] **Default to continuing**: After completing an activity, Claude now defaults to picking the next one
- [x] **Target 2-3 activities**: System prompt specifies completing multiple activities per session
- [x] **Clear stopping criteria**: Only stop after 3+ activities, 30+ minutes, or genuine blockers
- [x] **Anti-patterns listed**: Explicitly tells Claude NOT to close just because one activity is "done"

The instruction "Err on the side of doing more, not less" addresses the conservative exit behavior.

## Observed Results

Session 18 completed 3 activities (Project Notes → Sandbox → Tools). Session 19 in progress following same pattern.
