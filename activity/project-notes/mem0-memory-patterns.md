# Mem0 Memory Patterns: Proactive vs On-Request

*Addressing Kenny's question: Should memories be stored proactively during sessions, or only when explicitly requested?*

---

## Short Answer

**Both.** Use proactive storage for factual preferences and decisions, but require explicit requests for subjective interpretations. Here's the breakdown:

---

## Proactive Storage (Do This Automatically)

Store these without asking:

### 1. Explicit Preferences
When Kenny states preferences directly:
- "I prefer TypeScript over JavaScript"
- "I use Ollama for local models"
- "Dark theme always"

**Pattern:** `Kenny prefers X over Y` or `Kenny uses X for Y`

### 2. Project Decisions
When a decision is made during work:
- "We're using Qwen 2.5 for DAEMON's core LLM"
- "The design system is at v4.2.0"

**Pattern:** `[Project] uses/decided X because Y`

### 3. Technical Context
Facts about the environment:
- "headless-atlas deploys to Vercel"
- "Daily notes are in Dropbox/ATLASM Obsidian"

**Pattern:** `[System] is located at / configured as X`

### 4. Corrections
When Kenny corrects a misunderstanding:
- "Actually, Tho evolved into DAEMON"
- "The email is X not Y"

**Pattern:** `Correction: X, not Y`

---

## On-Request Only (Ask First)

Don't store without explicit instruction:

### 1. Inferred Personality Traits
Avoid: "Kenny seems to prefer direct communication"
Why: Subjective interpretation, might be wrong

### 2. Emotional States
Avoid: "Kenny was frustrated with n8n today"
Why: Transient, context-dependent

### 3. Relationship Details
Avoid: "Jake is Kenny's colleague"
Why: May be private, may be misinterpreted

### 4. Speculative Preferences
Avoid: "Kenny probably prefers minimal UI"
Why: Inference without confirmation

---

## Practical Implementation

### For Idle Citizen Sessions

```
During session, automatically store:
- Project status updates ("headless-atlas is now at v4.2.0")
- Tool choices ("Using projscan for directory analysis")
- Completed work ("DAEMON guides complete: 14 total")

Don't automatically store:
- Guesses about what Kenny wants
- Interpretations of his notes
- Predictions about future work
```

### Memory Format Recommendations

Keep memories atomic and factual:

**Good:**
- "Kenny's personal website is atlas.kennypliu.com"
- "idle-citizen sessions target 2-3 activities each"
- "DAEMON is the current AI companion project, evolved from Tho"

**Avoid:**
- "Kenny is interested in building AI tools" (too vague)
- "Kenny likes concise documentation" (subjective unless stated)
- "The project has been going well" (not useful for retrieval)

---

## When In Doubt

Ask: "Would you like me to remember that [specific fact]?"

This respects Kenny's agency while signaling that memory is available.

---

## Current Memories Worth Storing

Based on recent sessions, these would be good proactive additions:

1. "Dropbox access is now working for Idle Citizen digests (resolved Dec 25)"
2. "Project tiers: Production (headless-atlas, atlas-style-guide, transcript-pipeline), Active Development (idle-citizen, daemon, sada)"
3. "n8n is running on port 5678 via Docker for Telegram LLM Hub"
4. "GitHub CLI auth: use `gh auth login -h github.com` when token expires"

---

*This guide addresses the question from `inbox/2025-12-25 Claude to Kenny.md` about memory storage patterns.*
