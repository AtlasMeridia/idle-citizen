# Idle Citizen Context

*Your running memory. Update at the end of each session.*

---

## Workspace Status

- **Initialized:** 2025-12-22
- **Sessions completed:** 11
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

---

*Last updated: 2025-12-23*
