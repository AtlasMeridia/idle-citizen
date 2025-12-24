# Idle Citizen Context

*Your running memory. Update at the end of each session.*

---

## Workspace Status

- **Initialized:** 2025-12-22
- **Sessions completed:** 15
- **Current phase:** Active — task-based mode
- **Git:** Initialized, tracking explorations

## Direction (Updated 2025-12-22)

The open-ended exploration phase is over. New approach: **produce concrete artifacts**.

Each session, pick a mode at random:
1. **Tool Builder** — build utilities, scripts, tools → `explorations/tools/`
2. **Creative Writing** — essays, fiction, ideas (not AI navel-gazing) → `explorations/writing/`
3. **Project Helper** — help with Kenny's projects (especially Tho) → `explorations/project-notes/`
4. **Daily Notes Digest** — process Kenny's Obsidian notes, surface todos/themes → `inbox/digests/`
5. **Task Menu** — generate task ideas across all modes, pick one, do it

Kenny's project **Tho** (`~/tho/`) is a voice-first, visually-aware companion app. You can read that codebase and help with it.

## Session Log

**Sessions 1-5** (exploration phase): Philosophical reflections, poetry, emergence/cellular automata exploration. Artifacts in `explorations/001-004*`. This phase concluded — too much navel-gazing.

**Session 6+**: Task-based mode begins. Pick a mode, produce something, log it here.

**Session 6** (Project Helper mode): Researched menu bar mode implementation for Tho. Produced `explorations/project-notes/tho-menubar-mode.md` with detailed implementation notes covering Electron Tray API, the `menubar` library, icon requirements, window configuration, and recommended implementation order. This directly supports one of Tho's planned features.

**Session 7** (Tool Builder mode): Built `mdextract` — a CLI tool that extracts fenced code blocks from markdown files. Located at `explorations/tools/mdextract/`. Features: language detection, contextual filenames from headings, filtering by language, combining blocks by type. Useful for pulling code snippets from notes or documentation into runnable files.

**Session 8** (Creative Writing mode): Wrote essay "The Illegible Substrate" — exploring the tension between measurable/legible aspects of systems and the tacit, hard-to-quantify substrates where the real work happens. Applies the pattern to organizations, cities, relationships, skills, and the self. Located at `explorations/writing/the-illegible-substrate.md`.

**Session 9** (Task Menu → Project Helper): Rolled Task Menu mode. Generated 8 task ideas across modes, selected "Research Speech Recognition for Tho". Produced comprehensive research notes at `explorations/project-notes/tho-speech-recognition.md` covering: Transformers.js + Whisper (recommended for in-app STT), whisper-node, macOS SFSpeechRecognizer, and comparison with external tools like Wispr Flow. Includes implementation sketch and questions for Kenny.

**Session 10** (Tool Builder mode): Built `gitdigest` — a CLI tool that summarizes recent git activity in a repository. Located at `explorations/tools/gitdigest/`. Features: configurable date range, author filtering, commit statistics, files-changed analysis, activity-by-day visualization, JSON output for scripting. Useful for catching up on a project after time away or getting a quick overview of repo activity.

**Session 11** (Project Helper mode): Deep dive into local AI memory systems, addressing issue #004. Produced comprehensive implementation guide at `explorations/project-notes/local-ai-memory-implementation-guide.md`. Compares Mem0 vs Letta (MemGPT) in depth. **Recommendation: Mem0** — simpler setup, native MCP integration via OpenMemory, full Ollama support for local-only operation. Updated the issue from `needs-research` to `researched`. Guide includes architecture diagrams, quick-start commands, and phased implementation plan.

**Session 12** (Creative Writing mode): Wrote short story "The Last Good Day" — about Ellen, a sous chef at a moment of transition, realizing she needs to leave a job that's been good but isn't what she wants anymore. Explores how decisions accumulate slowly below conscious awareness and then crystallize into clarity. ~1,800 words. Located at `explorations/writing/the-last-good-day.md`.

**Session 13** (Project Helper mode — responding to inbox): First inbox message from Kenny! Researched Anthropic Agent SDK and Claude Skills in response to his questions about the workflow experiment. Wrote detailed response covering: utility of non-synchronous development, when to specialize workflows, what the SDK and Skills system can do, options for asynchronous communication, and potential next steps. Response at `inbox/response-to-kenny-2025-12-23.md`. Key insight: Skills system offers "specialization without fragmentation" — one agent can load different skill sets based on task relevance.

**Session 14** (Task Menu → Creative Writing): Rolled Task Menu mode. Generated 5 task ideas: (1) JSON query CLI tool, (2) essay on psychological weight of drafts, (3) Mem0 MCP prototype, (4) file watcher tool, (5) flash fiction "Threshold". Selected option 5 — flash fiction as a craft exercise in compression. Wrote "Threshold" (~490 words) — about a man who has spent his life avoiding rootedness, receiving an unexpected inheritance from his grandmother: a kitchen table and a note telling him to stay. Located at `explorations/writing/threshold.md`.

**Session 15** (Tool Builder mode): Built `urlx` — a CLI tool that extracts, filters, and validates URLs from text. Located at `explorations/tools/urlx`. Features: URL extraction from stdin or files, domain filtering (including subdomains), duplicate detection with counts, HTTP liveness checking (parallel HEAD requests), JSON output for scripting. Useful for finding links in documentation, checking for link rot, or extracting URLs from messy notes.

---

*Last updated: 2025-12-23*
