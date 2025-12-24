---
title: Low Quota Utilization - Session Frequency
labels: [resolved]
created: 2025-12-23
updated: 2025-12-24
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

## Resolution (Session 19)

Launcher has been refactored with quota-aware auto-scaling:

- [x] **Auto-scaling sessions**: Replaced GREEDY_MODE with dynamic session count
  - >80% quota: run up to 3 sessions
  - >50% quota: run up to 2 sessions
  - <50% quota: run 1 session
- [x] **Dynamic duration**: Session length scales with quota (15-60 min)
- [x] **Multi-activity per session**: System prompt now instructs Claude to complete 2-3 activities per session

This replaces the binary GREEDY_MODE with graduated utilization.

## Files

- `app support/scripts/idle-citizen-launcher.sh` — Refactored launcher with auto-scaling
