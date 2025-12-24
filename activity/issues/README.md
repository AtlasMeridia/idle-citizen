# Issues Activity

Maintain and work on the local issue tracker for Idle Citizen itself.

## Purpose

Track bugs, improvements, and ideas for the Idle Citizen system. This is meta-work—improving the tool that runs these sessions.

## Structure

- `open/` — Active issues (numbered .md files with YAML frontmatter)
- `closed/` — Resolved issues

## Issue Format

```yaml
---
title: Issue title
labels: [bug, enhancement, low-priority]
created: YYYY-MM-DD
---

Description of the issue...
```

## How to Execute

1. Review `open/` for existing issues
2. Pick one issue to work on (prefer higher priority, older issues)
3. Work on the issue:
   - For bugs: investigate, fix, test
   - For enhancements: implement or prototype
   - For research: investigate and document findings
4. If resolved, move the file to `closed/` and add a resolution note
5. If not resolved, update the issue with progress notes
6. Optionally: create new issues discovered during the session

## CLI Tool

There's an `issues` CLI tool in `activity/tools/issues` that can help manage issues:
- `issues list` — List open issues
- `issues show <id>` — Show details
- `issues new <title>` — Create issue
- `issues close <id>` — Close issue

## Success Criteria

- At least one issue receives meaningful progress
- Issue files are kept up to date with status
- New issues are captured when discovered

## Constraints

- Stay focused on Idle Citizen improvements (not external projects)
- Don't close issues without actually resolving them
