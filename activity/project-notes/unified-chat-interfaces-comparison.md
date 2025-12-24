# Unified Chat Interfaces for Interaction Data Architecture

*Research for local-first AI conversation aggregation*

---

## Summary

This note compares self-hosted chat UIs that could serve as a unified interface for AI interactions, specifically evaluating them for the **Interaction Data Architecture** initiative. The key question: which platform best supports capturing and aggregating all AI conversations in one place?

**Bottom line:** LibreChat is the best fit for Kenny's needs—multi-model support, conversation forking, and the upcoming admin panel will add conversation management. AnythingLLM has better local storage clarity (SQLite + JSONL export). Open WebUI is simplest for Ollama but lacks the aggregation focus.

---

## Candidates

### 1. LibreChat

**GitHub:** [danny-avila/LibreChat](https://github.com/danny-avila/LibreChat) (22k+ stars)

**What it does:** ChatGPT-style interface that connects to multiple AI providers through a single UI. Supports OpenAI, Anthropic, Azure, Groq, Mistral, OpenRouter, Vertex AI, Gemini, and any OpenAI-compatible API.

**Key features for data architecture:**
- **Multi-model switching mid-conversation** — Switch providers within a single chat
- **Conversation forking** — Explore different response paths, preserving history
- **MCP support** — Can integrate with tools like Mem0
- **Artifacts** — Like Claude's artifacts feature
- **Custom endpoints** — No proxy needed for OpenAI-compatible APIs

**2025 Roadmap highlights:**
- Admin panel as separate CMS app for managing usage, chats, users
- Agent Marketplace (GPTs-style sharing)
- Hosted version coming Q3 2025

**Storage:** Uses MongoDB by default. Conversation data is queryable but format isn't documented for export.

**Deployment:** Docker, npm, Helm charts for Kubernetes

---

### 2. Open WebUI

**GitHub:** [open-webui/open-webui](https://github.com/open-webui/open-webui) (Previously "Ollama WebUI")

**What it does:** Started as Ollama frontend, evolved into general-purpose LLM interface. Strong local-first focus.

**Key features:**
- **Native Ollama integration** — Create/manage Ollama models directly in UI
- **OpenAI API compatibility** — Connect to cloud providers too
- **Works entirely offline** — No network required once models downloaded
- **PWA support** — Mobile-friendly
- **Lightweight** — Minimal latency, efficient

**Storage:** Less documented than LibreChat. Focuses on real-time use rather than data aggregation.

**Deployment:** Docker, Kubernetes with Helm/Kustomize

**Limitation:** Less suited for multi-provider aggregation. Better for local-only or single-provider use.

---

### 3. AnythingLLM

**GitHub:** [Mintplex-Labs/anything-llm](https://github.com/Mintplex-Labs/anything-llm)

**What it does:** "All-in-one AI desktop app" — goes beyond chat to include RAG, agents, and document interaction.

**Key features:**
- **SQLite local database** — `anythingllm.db` stores all data locally
- **JSONL export** — Chat history exportable in fine-tuning format
- **Workspaces** — Organize conversations by project/context
- **RAG built-in** — Chat with documents, uses LanceDB for vectors
- **Agents** — Local AI agents that interact with files and databases

**Storage location (macOS):**
```
~/Library/Application Support/anythingllm-desktop/storage/
├── anythingllm.db      # SQLite database (all chats)
├── vector-cache/       # Embedded document representations
└── models/             # Local GGUF models
```

**Export:** Admin can export all chat history as JSONL (designed for fine-tuning OpenAI models, but useful for archival).

**Deployment:** Desktop app (Electron) or Docker (map `/app/server/storage` for persistence)

---

### 4. LobeChat

**What it does:** Lightweight, design-focused chat UI with modern aesthetics. Extensible plugin architecture.

**Key features:**
- PWA support
- Image generation, TTS, STT integrations
- Multi-model support
- Clean, modern UI

**Storage:** Less emphasis on data persistence/export. More consumer-focused than enterprise/archival.

---

## Comparison Matrix

| Feature | LibreChat | Open WebUI | AnythingLLM |
|---------|-----------|------------|-------------|
| Multi-provider support | Excellent | Good | Good |
| Local model support | Via API | Native Ollama | Native |
| Storage format | MongoDB | Undocumented | SQLite |
| Chat export | TBD (admin panel coming) | Limited | JSONL |
| MCP support | Yes | No | No |
| Conversation forking | Yes | No | No |
| RAG/documents | Plugin-based | Limited | Built-in |
| Desktop app | No (web only) | No | Yes |
| Complexity | Medium | Low | Medium |

---

## Recommendation for Interaction Data Architecture

### Primary: LibreChat

**Why:**
1. **Best multi-provider aggregation** — Can consolidate Claude, GPT-4, Mistral, local Ollama models in one interface
2. **Conversation forking** — Preserves alternative paths (useful for archival)
3. **MCP support** — Can integrate Mem0 or other memory systems
4. **Active development** — 22k+ stars, dedicated team, clear 2025 roadmap
5. **Upcoming admin panel** — Will add conversation management features

**Trade-offs:**
- MongoDB adds complexity vs SQLite
- Export format not yet well-documented
- Web-only (no desktop app)

### Secondary: AnythingLLM (for local/document focus)

**Why:**
- SQLite is simpler to query than MongoDB
- JSONL export is clear and portable
- Better for RAG/document workflows
- Desktop app option

**Trade-offs:**
- Weaker multi-provider story
- No conversation forking
- Less active development than LibreChat

### Skip: Open WebUI

- Best for Ollama-only setups
- Doesn't solve the aggregation problem
- Storage/export not a priority

---

## Integration with Existing Architecture

If using LibreChat as the unified interface:

1. **Route all AI interactions through LibreChat**
   - Claude API → LibreChat custom endpoint
   - GPT-4 → LibreChat OpenAI endpoint
   - Ollama → LibreChat local endpoint

2. **Export from LibreChat to SQLite/Markdown**
   - MongoDB can be queried directly
   - Build exporter script (similar to cchistory for Claude Code)
   - Store rendered conversations in Obsidian

3. **Keep Claude Code separate**
   - CLI workflows don't fit web UI model
   - Use cchistory to extract Claude Code conversations
   - Merge into unified store alongside LibreChat exports

4. **Official exports as backup**
   - Periodic claude.ai export (official)
   - Merge with LibreChat data

---

## Open Questions

1. **Claude Desktop integration** — Can LibreChat intercept Claude Desktop conversations? (Probably not—Desktop uses proprietary sync)

2. **LibreChat MongoDB schema** — What's the actual conversation format? Need to deploy and inspect.

3. **Real-time vs batch** — Should conversations flow through LibreChat live, or continue using native apps and batch-aggregate?

4. **Perplexity** — Still no solution for capturing Perplexity interactions. May need browser extension.

---

## Sources

- [LibreChat GitHub](https://github.com/danny-avila/LibreChat)
- [LibreChat 2025 Roadmap](https://www.librechat.ai/blog/2025-02-20_2025_roadmap)
- [LibreChat vs Open WebUI Comparison](https://portkey.ai/blog/librechat-vs-openwebui/)
- [Open WebUI Alternatives](https://www.helicone.ai/blog/open-webui-alternatives)
- [AnythingLLM Desktop Storage](https://docs.anythingllm.com/installation-desktop/storage)
- [AnythingLLM Chat Logs Export](https://docs.anythingllm.com/features/chat-logs)
- [5 Best Open Source Chat UIs 2025](https://poornaprakashsr.medium.com/5-best-open-source-chat-uis-for-llms-in-2025-11282403b18f)
- [Top Open-Source ChatGPT Interfaces Comparison](https://blog.elest.io/the-best-open-source-chatgpt-interfaces-lobechat-vs-open-webui-vs-librechat/)

---

*Generated 2025-12-24 by Claude (Idle Citizen project-notes activity)*
