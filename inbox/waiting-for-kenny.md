# Waiting for Kenny

*Items blocked pending your input. Updated automatically by Claude.*

---

## Open Issues

### #003 — Dashboard for Reviewing Session Activity
**Status:** Prototype built, waiting for testing
**Created:** 2025-12-23 | **Last updated:** 2025-12-24

**Prototype location:** `activity/tools/dashboard/`

A working dashboard exists with:
- Summary cards (total sessions, time, quota %, artifacts)
- Daily activity chart
- Issues visualization
- Recent commits list
- Recent artifacts section (10 most recent with titles)

**What I need from you:**
1. Run `./activity/tools/dashboard/view.sh` to test
2. Let me know if it works and what's missing
3. Decide on update frequency: on-demand, auto-refresh after sessions, or real-time?

---

### Response
Hmm. I'm not crazy about. We should shelve this. I'

---

### #004 — Local AI Memory System
**Status:** Research complete, awaiting decision
**Created:** 2025-12-23

**Research:** `activity/project-notes/local-ai-memory-implementation-guide.md`

**Recommendation:** Mem0 with OpenMemory MCP server, fully local with Ollama.

**What I need from you:**
1. Should memory be shared across all projects or per-project?
2. Ready to proceed with Mem0 setup, or want to explore alternatives?

---

### ~~#005 — Sensitive Credentials File in Repo~~ RESOLVED
File has been removed from repo root. Closed in Session 37.

---

## Blocked Activities

### Headless-Atlas — Pending Items

**5 commits ahead of origin** — you need to push when ready.

**Email marketing integration:**
- Plan exists for Kit.com + Zapier workflow
- Blocked: requires you to create Kit.com and Zapier accounts

**Site content edits:**
- Copy options provided in `~/Projects/headless-atlas/dev/copy-options.md` (or similar)
- Blocked: waiting for you to select preferred copy

---

### Digests Activity — Symlink Inaccessible

The daily notes symlink points to Dropbox but Claude Code can't access it due to sandbox permissions:
```
activity/digests/daily-notes -> /Users/ellis/Library/CloudStorage/Dropbox/...
```

**Options to fix:**
1. **Copy files manually** — copy daily notes into `activity/digests/daily-notes/` instead of symlinking
2. **Grant sandbox access** — adjust permissions for Claude Code to access Dropbox
3. **Alternative location** — put daily notes somewhere Claude can read them

This has been blocking digests processing for multiple sessions.

---

## DAEMON Research Complete

The full DAEMON implementation research suite (12 guides) is done. No blockers — just FYI that it's ready when you are:

1. Phase 1 Implementation
2. R&D Agent
3. TTS (Local)
4. VLM (Local)
5. Personality Configuration
6. LLM Selection
7. MCP/Tools
8. Orchestrator
9. Interface
10. Data Ingestion
11. Intent/Goal Tracking

All in `activity/project-notes/daemon-*.md`

---

*Last updated: 2025-12-24 (Session 37)*
