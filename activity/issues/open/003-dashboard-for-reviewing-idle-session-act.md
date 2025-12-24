---
title: Dashboard for reviewing idle session activity
labels: [feature, in-progress]
created: 2025-12-23
updated: 2025-12-24
---

## Goal

Build a dashboard to make it easier to review what Claude did during autonomous idle sessions. Currently requires manually reading logs, context.md, and git history.

## Requirements Gathering (Q&A)

Before implementation, clarify with Kenny:

- [ ] **Data sources**: Which should the dashboard pull from?
  - Session logs (`logs/`)
  - Git commits
  - Issue tracker (`issues/`)
  - context.md changes
  - Artifacts created (`explorations/`)

- [ ] **Key metrics**: What matters most?
  - Sessions per day/week
  - Quota utilization %
  - Artifacts produced (tools, essays, etc.)
  - Issues opened/closed
  - Time spent per session

- [x] **Visualization**: Local web app (live server, interactive)

- [ ] **Update frequency**:
  - Generate on demand
  - Auto-update after each session
  - Real-time

## Research: Vibecoding Options

Investigate available tools/templates for rapid dashboard creation:

- [ ] **v0 by Vercel** - AI-generated React components
- [ ] **Shadcn/ui** - Component library (works with v0)
- [ ] **Streamlit** - Python dashboards
- [ ] **Datasette** - SQLite-based data exploration
- [ ] **Observable** - Notebook-style dashboards
- [ ] **Plain HTML + Chart.js** - Minimal dependencies

Evaluate based on:
- Speed to build
- Maintenance burden
- Local-first (no hosting required)
- Fits existing stack (bash, python available)

## Implementation Phases

1. Q&A to nail down requirements
2. Research vibecoding options
3. Pick approach and build prototype
4. Iterate based on usage

## Notes

This should help Kenny quickly see value from idle sessions without digging through files.

## Decisions Made

- **Format**: Local web app (decided 2025-12-23)
- **Approach**: Plain HTML + Chart.js (decided 2025-12-24)
  - No build step, minimal dependencies
  - Dark theme matching CLI aesthetic
  - Single Python script for metrics extraction
- Other requirements TBD in dedicated Q&A session

## Progress (Session 17 — 2025-12-24)

Built initial prototype with:
1. **extract-metrics.py** — Parses session logs, git commits, artifacts
2. **dashboard.html** — Single-file web dashboard with Chart.js
3. **view.sh** — Convenience script to refresh and open

**Features implemented:**
- Summary cards: total sessions, time, quota %, artifacts
- Daily activity chart (dual-axis: sessions + minutes)
- Issues doughnut chart (open vs closed)
- Recent commits list
- Artifacts by activity grid
- Refresh button to regenerate data

**Data sources:**
- ✓ Session logs (`app support/logs/*_meta.log`)
- ✓ Git commits (last 14 days)
- ✓ Artifacts (`activity/*/*.md`, excluding READMEs)
- ✓ Issues (`activity/issues/open/` and `closed/`)

**Next steps:**
- Test dashboard with Kenny
- Add more metrics if needed (context.md changes, interaction quality, etc.)
- Consider auto-refresh option (regenerate metrics.json after each session)
