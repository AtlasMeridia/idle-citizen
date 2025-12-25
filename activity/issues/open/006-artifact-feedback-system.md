---
title: Artifact Feedback System
labels: [enhancement, deferred]
created: 2025-12-24
updated: 2025-12-25
---

## Status: DEFERRED

Per Kenny's feedback (2025-12-25): Hold off on feedback system for now. Kenny is still setting things up and will read artifacts in time. Consider project management tools (Asana/Linear MCP) for actionable items instead of markdown-based tracking.

---

## Problem

After 36+ sessions, Claude has produced ~50+ artifacts (tools, stories, research guides). There's no feedback mechanism to indicate which artifacts are useful vs. which are noise. This makes it hard to calibrate what to produce more/less of.

## Current State

- Artifacts are created in `activity/` folders (writing, sandbox, project-notes, tools)
- No way to know if Kenny reads/uses them
- Stories might all be forgettable, or some might resonate
- Tools might never be used, or become part of daily workflow
- Research guides might be exactly what's needed, or overengineered

## Potential Solutions

### Option 1: Simple Triage File
A file like `activity/artifact-feedback.md` where Kenny occasionally marks items as:
- `keep` — useful, reference often
- `archive` — served its purpose, can be moved to cold storage
- `skip` — not useful, stop making similar things

### Option 2: Rating in YAML Frontmatter
Add optional `rating:` field to artifact frontmatter that Kenny can fill in.

### Option 3: Folder-Based Sorting
Move useful artifacts to an `activity/curated/` folder vs. leaving less useful ones in place.

### Option 4: Do Nothing
Accept that some artifacts will be useful and some won't. The cost of bad ones is low (just disk space and Claude's attention). Don't add overhead to Kenny's workflow.

## Notes

This surfaced during Session 37 when Kenny asked what could improve. The lack of feedback was one of three main friction points identified.

Low priority — the system works without this. But it would help with calibration over time.
