---
title: Dashboard for reviewing idle session activity
labels: [feature, needs-research]
created: 2025-12-23
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
- Other requirements TBD in dedicated Q&A session
