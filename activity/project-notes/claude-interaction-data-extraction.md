# Claude Interaction Data Extraction

*Research for the Interaction Data Architecture initiative*

---

## Summary

This note covers how to extract conversation data from three Claude interfaces:
1. **Claude Desktop** (Electron app)
2. **Claude.ai** (web browser)
3. **Claude Code** (CLI)

**Bottom line:** Claude Code data is fully accessible locally. Claude Desktop/web data is harder—LevelDB caches exist locally but aren't designed for extraction. The official export is available but clunky.

---

## Claude Code (CLI) — Easy

Claude Code stores all conversations locally in `~/.claude/`. This is the most accessible source.

### Storage Location

```
~/.claude/
├── history.jsonl         # Index of all prompts (timestamps, project, session IDs)
├── projects/             # Full conversations, organized by project path
│   └── -Users-kenny-Projects-foo/
│       ├── abc123.jsonl  # One JSONL file per conversation
│       └── agent-*.jsonl # Sub-agent conversations
├── todos/                # Todo lists from sessions
└── file-history/         # Files modified across sessions
```

### Format

Each conversation is a JSONL file. The `history.jsonl` is a simple index:

```json
{"display":"user message","pastedContents":{},"timestamp":1766449705858,"project":"/path/to/project","sessionId":"uuid"}
```

Full conversation files contain complete request/response pairs with tool calls, function results, etc.

### Extraction Approach

For Claude Code, simply:
1. Copy/parse JSONL files from `~/.claude/projects/`
2. Join with `history.jsonl` for timestamps and session grouping
3. Filter by project or date range as needed

**Tools that exist:**
- [claude-conversation-extractor](https://pypi.org/project/claude-conversation-extractor/) — Python CLI for extracting and searching Claude Code history
- [claude-code-history-viewer](https://github.com/jhlee0409/claude-code-history-viewer) — macOS app for browsing conversations

---

## Claude Desktop (Electron App) — Hard

Claude Desktop uses Chromium's LevelDB for local storage, but conversations appear to sync server-side rather than being stored locally in full.

### Storage Location

```
~/Library/Application Support/Claude/
├── Local Storage/leveldb/    # LevelDB database
├── Session Storage/          # Also LevelDB
├── config.json               # User preferences (theme, locale)
├── claude_desktop_config.json # MCP server configuration
└── Preferences               # Spellcheck settings, zoom levels
```

### What's Actually There

The LevelDB stores appear to contain:
- Session state (UI state, not full conversations)
- Auth tokens and caching
- Local preferences

**Conversations are primarily server-side.** The Desktop app syncs with claude.ai—"Your conversations, projects, memory, and preferences sync across all devices when you're signed in."

### Reading LevelDB (if needed)

Python options for reading Chromium LevelDB:
- [ccl_chromium_reader](https://github.com/cclgroupltd/ccl_chrome_indexeddb) — Pure Python, handles Chrome's specific LevelDB format
- [plyvel](https://plyvel.readthedocs.io/) — Generic LevelDB bindings (requires libleveldb)

Example with ccl_chromium_reader:
```python
import pathlib
from ccl_chromium_reader import ccl_chromium_localstorage

db_path = pathlib.Path("~/Library/Application Support/Claude/Local Storage/leveldb")
with ccl_chromium_localstorage.LocalStoreDb(db_path.expanduser()) as local_storage:
    for storage_key in local_storage.iter_storage_keys():
        for record in local_storage.iter_records_for_storage_key(storage_key):
            print(record)
```

**Caveat:** Even if you read the LevelDB, full conversations likely aren't there.

---

## Claude.ai (Web) — Medium

Web conversations can be exported officially or scraped from the browser.

### Official Export

1. Go to Settings > Privacy
2. Click "Export data"
3. Receive email with download link (expires in 24 hours)
4. Download ZIP containing JSON files

**Limitations:**
- Manual process, not scriptable
- Deleted conversations are excluded
- Format is JSON but structure isn't documented

### Browser-Based Extraction

[Claude Export (browser script)](https://github.com/ryanschiang/claude-export) — Run in DevTools to export the currently open conversation to Markdown, JSON, or PNG.

[Claude Exporter (Chrome extension)](https://chromewebstore.google.com/detail/claude-exporter-save-clau/elhmfakncmnghlnabnolalcjkdpfjnin) — Export to PDF, Markdown, Text, CSV, or JSON.

These work on individual conversations, not bulk export.

---

## Recommendation for Interaction Data Architecture

### Phase 1: Start with Claude Code

Claude Code is the low-hanging fruit:
- Full local access, no API needed
- Well-structured JSONL format
- Already tied to projects (context is preserved)
- Covers the most technical/development conversations

**Build:**
1. Python script to parse `~/.claude/projects/` → structured output
2. Filter by date range, project, or keywords
3. Store in SQLite or render to Markdown for Obsidian

### Phase 2: Official Export for claude.ai/Desktop

For non-Code conversations:
1. Use official export periodically (monthly?)
2. Parse the JSON structure from exports
3. Merge into unified store

The export format isn't documented, so this requires reverse-engineering one export to understand the schema.

### Phase 3: (Optional) Real-time capture

If real-time capture is desired:
- **Claude.ai:** Browser extension could intercept responses
- **Claude Desktop:** MCP server could log interactions (but only for tool calls, not general chat)

This adds complexity. Start with batch extraction.

---

## Open Questions

1. **Export format:** What exactly is in the official export ZIP? Need to run one to document the structure.

2. **Desktop local cache:** Is there useful data in the LevelDB beyond session state? Worth a deeper look with ccl_chromium_reader.

3. **API access:** Does Anthropic plan to add conversation history to the API? (Currently no.)

4. **Perplexity:** The design doc excluded Perplexity—is there a local storage location for that too?

---

## Sources

- [How can I export my Claude data?](https://support.claude.com/en/articles/9450526-how-can-i-export-my-claude-data) — Official Anthropic docs
- [claude-conversation-extractor](https://github.com/ZeroSumQuant/claude-conversation-extractor) — Python tool for Claude Code
- [claude-code-history-viewer](https://github.com/jhlee0409/claude-code-history-viewer) — macOS app
- [ccl_chromium_reader](https://github.com/cclgroupltd/ccl_chrome_indexeddb) — Python LevelDB reader
- [claude-export](https://github.com/ryanschiang/claude-export) — Browser console script

---

*Generated 2025-12-24 by Claude (Idle Citizen project-notes activity)*
