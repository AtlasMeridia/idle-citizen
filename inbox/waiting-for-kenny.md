# Waiting for Kenny

*Items blocked pending your input. Updated automatically by Claude.*

---

## Open Issues

### #004 — Local AI Memory System
**Status:** Research complete, awaiting decision
**Created:** 2025-12-23

**Research:** `activity/project-notes/local-ai-memory-implementation-guide.md`

**Recommendation:** Mem0 with OpenMemory MCP server, fully local with Ollama.

**What I need from you:**
1. Should memory be shared across all projects or per-project?
2. Ready to proceed with Mem0 setup, or want to explore alternatives?

---

### #006 — Artifact Feedback System
**Status:** Proposal awaiting input
**Created:** 2025-12-24

Proposed a way for you to signal which artifacts are useful (simple rating in frontmatter). Low priority — see issue for details.

---

## Resolved This Session

### ~~#003 — Dashboard for Reviewing Session Activity~~ SHELVED
Per your feedback: "I'm not crazy about [this]. We should shelve this."

Done:
- Moved prototype to `app support/archived/dashboard/`
- Closed issue #003 with resolution notes
- For now, session visibility will use markdown files in inbox as you suggested

### ~~#005 — Sensitive Credentials File in Repo~~ RESOLVED
File was removed from repo. Closed in Session 37.

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

The full DAEMON implementation research suite (14 guides) is done. No blockers — just FYI that it's ready when you are:

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
12. Aesthetic Memory Architecture
13. Claude Agent SDK Integration
14. **Privacy & Security** (new — encryption, key management, threat model)

All in `activity/project-notes/daemon-*.md`

---

*Last updated: 2025-12-24 (Session 38)*
