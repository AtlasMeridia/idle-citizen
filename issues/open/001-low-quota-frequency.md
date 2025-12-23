---
title: Low Quota Utilization - Session Frequency
labels: [bug, high-priority]
created: 2025-12-23
---

## Problem

Only using ~3% of weekly quota. Launchd triggers sessions every 2 hours, but:
- `GREEDY_MODE=false` (default) — runs ONE session per trigger, then waits 2 hours
- Sessions complete in 2-5 minutes despite 60-minute timeout
- Net result: ~3-5 minutes of usage every 2 hours

## Root Cause

Combination of:
1. 2-hour `StartInterval` in launchd plist
2. `GREEDY_MODE=false` — no session chaining
3. Sessions exit after completing one task (see issue #002)

## Potential Fixes

- [ ] Enable `GREEDY_MODE=true` in launchd plist to chain sessions until quota exhausted
- [ ] Reduce `StartInterval` from 7200s (2hr) to something shorter
- [ ] Both

## Files

- `/Users/ellis/Library/LaunchAgents/com.claude-space.launcher.plist`
- `/Users/ellis/Projects/claude-space/claude-space-launcher.sh`
