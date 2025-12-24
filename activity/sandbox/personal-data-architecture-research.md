# Personal Data Architecture: A Comprehensive Survey (December 2024)

*Synthesis of research on personal knowledge systems, AI memory, and data capture pipelines*

---

## Executive Summary

The convergence of three technology trends is creating a new category: **personal data architecture**—systems that capture, organize, and make queryable an individual's digital life.

1. **Personal Knowledge Graphs** — Tools like Obsidian, Logseq, and Mem that organize notes with linking and AI assistance
2. **AI Memory Systems** — Frameworks like Mem0, Zep, and MemGPT that give AI assistants persistent, personalized memory
3. **Data Capture Pipelines** — Tools like Screenpipe, ActivityWatch, and Simon Willison's Dogsheep that aggregate activity across platforms

This research synthesizes the state of the art across all three domains, with focus on what's actually working (vs. vaporware) and practical implementation patterns.

---

## Part I: Personal Knowledge Graphs

### The Current Landscape

The "second brain" space has matured from early tools like Roam Research into a diverse ecosystem. The dominant pattern combines:

- **Vector embeddings** for semantic search
- **Graph databases** for relationship mapping
- **Local-first storage** for privacy and ownership

**Tools by Architecture:**

| Tool | Storage | Graph | Vectors | Local-First |
|------|---------|-------|---------|-------------|
| Obsidian | Markdown files | Plugin-based | Plugins | Yes |
| Logseq | Markdown/SQLite | Native | Planned | Yes |
| Mem AI | Cloud | Native "Mem Graph" | Native | No |
| Notion | Postgres-based | Via AI Connectors | Native | No |
| Reflect | Cloud | Bidirectional links | GPT-4 powered | No |
| Khoj | Self-hosted | Separate project | Native | Yes |

### What's Working

**Obsidian's Plugin Ecosystem** — 1000+ plugins prove the value of extensibility. Notable:
- **Graph Analysis**: similarity, link prediction, community detection
- **InfraNodus**: network science algorithms, betweenness centrality
- **Dataview**: turns notes into queryable database
- **Web Clipper** (Nov 2024): AI-powered capture with Ollama support

**Logseq's Database Version** — October 2025 beta replaces file-based storage with SQLite for improved performance. Real-time collaboration in alpha.

**Notion 3.0 Agents** (September 2025) — The most ambitious integration play:
- Agents capable of 20+ minute autonomous actions
- Connectors to Slack, Google Drive, GitHub, Teams
- Multi-model access (GPT-5, Claude Opus 4.1, o3)
- MCP integrations with Perplexity, HubSpot, Lovable

### What's Vaporware

**Microsoft Recall** — A year of delays since the May 2024 announcement. The initial plaintext database was a security disaster. Now rolling out (April 2025) as opt-in only, but trust is damaged. Not available in the EEA.

**Most "AI-powered" promises** — Look for: no technical specifics, closed source with privacy claims but no audit, acquisition without product continuation.

### Emerging Patterns

**Temporal Knowledge Graphs** — [Graphiti](https://github.com/getzep/graphiti) (from Zep) implements bi-temporal data: tracks both when events occurred AND when they were ingested. Four timestamps per fact:
- `t' created` / `t' expired`: System tracking
- `t valid` / `t invalid`: Factual validity range

This enables questions like "What did I believe about X in March?" separate from "What do I now know is true about X?"

**Quantified Cognition** — The quantified self movement (step counts, sleep metrics) is evolving toward tracking cognitive patterns. AI enables transformation from raw metrics to narrative understanding. The tools capturing "everything you see and hear" (Screenpipe, Recall) provide the infrastructure; LLMs extract meaning.

---

## Part II: AI Memory Systems

### Commercial Memory Features

**ChatGPT Memory** (April 2024, expanded 2025)
- Two-tier: "Saved memories" (explicit) + "Chat history reference" (implicit)
- RAG-based architecture sitting outside the LLM
- Plus/Pro users can reference all past conversations

**Claude Memory** (August-October 2025)
- Project-based isolation (unlike ChatGPT's global memory)
- File-based system: memory stored in Markdown (CLAUDE.md)
- Import/export tools for migrating from ChatGPT or Gemini
- Deliberately simple—avoids complex vector databases

**Google Gemini Memory** (November 2024 - August 2025)
- Playing catch-up despite access to vast user data
- August 2025: automatic memory enabled by default
- Deliberately cautious about personalization

### Open-Source Memory Frameworks

**Mem0** — The leader. $24M Series A (October 2025).
- Hybrid architecture: graph + vector + key-value stores
- Dynamic forgetting, memory consolidation
- Claims +26% accuracy over OpenAI Memory (LOCOMO benchmark)
- MCP integration via OpenMemory
- 3 lines of code to integrate

**Letta/MemGPT** — Production framework from the MemGPT research paper.
- Treats LLMs as operating systems with virtual context management
- Two-tier: in-context (main) and out-of-context (external)
- Self-editing memory: LLM actively manages its own memory using tools
- "Heartbeat" mechanism for multi-step reasoning

**Zep** — Claims state-of-the-art performance.
- Temporal knowledge graph via Graphiti engine
- Sub-200ms latency
- Maintains multiple temporal versions of facts
- 94.8% on DMR benchmark vs MemGPT's 93.4%

**LangMem** — LangChain's official solution (early 2025).
- Three memory types: semantic, episodic, procedural
- Native LangGraph integration
- Background manager for automatic extraction/consolidation
- PostgreSQL and MongoDB persistence

**Memobase** — User profile-focused, open source.
- Similar to ChatGPT's memory architecture
- <100ms latency, fully dockerized
- Claims SOTA on LOCOMO benchmark (v0.0.37)

### Vector Database Choices

| Database | Best For | Notes |
|----------|----------|-------|
| **Chroma** | Prototyping | Simplest to start |
| **Qdrant** | Production RAG | Best metadata filtering; used by Discord, Perplexity |
| **Weaviate** | Knowledge graphs + semantic search | Multimodal support |
| **pgvector** | Existing PostgreSQL | Degrades >10M vectors |
| **Milvus** | Maximum scale | Billions of vectors |

Most frameworks abstract vector stores, making migration relatively easy.

### RAG vs. Fine-Tuning vs. Context Injection

| Approach | Best For |
|----------|----------|
| **RAG** | Dynamic knowledge, traceable sources |
| **Fine-Tuning** | Stable domain knowledge, behavioral changes |
| **Context Injection** | Session-specific personalization |

**2025 Trend: Hybrid.** Fine-tune for voice/expertise, RAG for real-time data, context injection for immediate state.

### Memory Architecture Patterns

**Episodic vs. Semantic Memory**
- Episodic: Specific past interactions, time-bound ("In December you mentioned...")
- Semantic: General facts, context-detached ("User prefers tea")
- MemGPT implements "semantization"—transforming episodic into semantic over time

**Forgetting Mechanisms**
- Ebbinghaus decay (MemoryBank): time-based forgetting
- Strategic forgetting (MemGPT): summarization, targeted deletion
- Temporal invalidation (Zep): explicit fact expiration

"Forgetting isn't a flaw—it's a feature of intelligent memory."

---

## Part III: Data Capture Pipelines

### Screen/Activity Capture

**Screenpipe** (Open Source, VC-backed)
- 24/7 screen + mic capture, 100% local, Rust
- OCR, Whisper transcription, Ollama integration
- Plugin system ("Pipes") for custom apps
- #1 GitHub trending repo, twice (late 2024)

**ActivityWatch** (Open Source)
- Cross-platform time tracking
- Tracks: active app, window titles, browser tabs, AFK
- All local with REST API
- Actively maintained by Erik and Johan Bjäreholt

**Limitless** (formerly Rewind AI)
- Pivoted from desktop capture to wearable pendant ($99-$199)
- 100-hour battery, continuous recording
- Meta acquired in December 2024

**Apple Intelligence** (iOS 18.1+)
- On-device processing as privacy cornerstone
- Personal context for Siri ("When is Mom's flight?")
- Private Cloud Compute for complex requests

### Browser History Aggregation

**Chrome Semantic Search** (August 2024)
- Native "history embeddings" feature
- 1540-dimensional vectors for semantic similarity
- Natural language queries: "that ice cream shop last week"

**DIY Pattern**
- Chrome extension for capture
- FastAPI backend
- Ollama for local embeddings (mxbai-embed-large)
- FAISS vector index

**Obsidian Web Clipper** (November 2024)
- Saves to local vault
- AI Interpreter: use LLMs to transform during capture
- Ollama, Claude, ChatGPT compatible

### Conversation Capture

**Texts** / **Beeper** — Multi-platform aggregators (WhatsApp, Messenger, Telegram, Signal, Slack, Discord, iMessage). Messages never leave device.

**Granola** (May 2024, $20M Series A late 2024)
- Captures system audio (no bot joins calls)
- Combines your notes with AI-generated notes
- Audio deleted after transcription

### File System Indexing

**Fenn** (macOS)
- Semantic search: "dog with birthday hat"
- Searches spoken words in audio/video
- Local processing

**Traditional**: HoudahSpot, EasyFind, DocFetcher

### API Aggregation

**Dogsheep** (Simon Willison)
- Philosophy: convert personal data to SQLite, query with Datasette
- Tools: `twitter-to-sqlite`, `healthkit-to-sqlite`, `google-takeout-to-sqlite`
- Query everything in a web interface
- Data stays on your device

**QS Ledger**
- Python/Jupyter for personal data
- Apple Health, Fitbit, GoodReads, Google Calendar, Instapaper
- Analysis with Pandas, NumPy, Matplotlib

### Privacy Spectrum

| Approach | Examples | Trade-off |
|----------|----------|-----------|
| Fully Local | ActivityWatch, Screenpipe | Max privacy, limited AI |
| Hybrid Encrypted | Limitless, Apple Intelligence | Better AI, requires trust |
| Cloud-Dependent | Heyday, Mem.ai | Best AI, data leaves device |

---

## Architectural Synthesis: The Personal Data Stack

Based on this research, a comprehensive personal data architecture would have layers:

### Layer 1: Capture

Multiple ingestion points, all feeding local storage:

- **Screen/Audio**: Screenpipe or ActivityWatch
- **Browser**: Web clipper + semantic history
- **Conversations**: Granola for meetings, export tools for chat
- **Files**: Local indexer with OCR
- **APIs**: Dogsheep-style converters for services

### Layer 2: Storage

SQLite as the unifying format (echoed across Dogsheep, Screenpipe, Logseq DB):

- **Raw data**: SQLite databases per source
- **Embeddings**: Local vector store (Qdrant or Chroma)
- **Graph**: Relationships in Neo4j or embedded in SQLite

### Layer 3: Memory

AI memory framework for synthesis:

- **Mem0** for the hybrid graph+vector+key-value approach
- OR **Zep/Graphiti** for temporal reasoning
- OR **LangMem** if in the LangChain ecosystem

### Layer 4: Interface

Query and interaction:

- **Datasette** for raw data exploration
- **Claude/ChatGPT/local LLM** with memory integration
- **Dashboard** for visualization

### Layer 5: Sync (Optional)

If multi-device access is needed:

- CRDTs for conflict-free local-first sync
- Client-side encryption before any cloud storage
- Encrypted cloud as backup, never as source of truth

---

## Implementation Priorities for Interaction Data Architecture

Based on Kenny's existing work and this research:

### Phase 1: Claude Code Extraction (Already Done)
- `cchistory` tool built in Session 18
- JSONL format is well-structured
- Good foundation for the capture layer

### Phase 2: Local Memory Integration
**Recommended: Mem0**
- Native MCP integration
- Works with Ollama for fully local operation
- Simple to start (3 lines of code)
- Already researched in detail (issue #004, Session 11)

### Phase 3: Multi-Source Capture
- Add browser history via Chrome extension or Obsidian Web Clipper
- Consider ActivityWatch for activity context
- Screenpipe if willing to do full screen capture

### Phase 4: Unified Query Interface
- LibreChat recommended for multi-provider chat (Session 19 research)
- Could integrate Mem0 as memory backend
- Dashboard for visualization (prototype exists from Session 17)

### Phase 5: Temporal Reasoning
- Evaluate Zep/Graphiti for temporal knowledge graph
- Would enable queries like "What did I think about X last month?"

---

## Key Insights

1. **SQLite is the lingua franca** — The most successful tools (Dogsheep, Screenpipe, Logseq DB) converge on SQLite. It's queryable, portable, and needs no server.

2. **Local-first is winning** — Privacy concerns and the Recall backlash are pushing adoption toward on-device processing. Apple Intelligence and Screenpipe represent different implementations of the same principle.

3. **Memory is becoming a layer** — AI memory is moving from baked-in features (ChatGPT) to swappable layers (Mem0, Zep). This enables custom architectures.

4. **Temporal reasoning is immature** — Most tools treat data as static. Graphiti is the main exception. This is an opportunity space.

5. **The capture problem is largely solved** — Tools exist for every data source. The unsolved problem is synthesis and retrieval.

6. **Hybrid architectures are the trend** — Vector (for semantics) + Graph (for relationships) + Key-Value (for facts). No single data model suffices.

---

## Sources

### Personal Knowledge Graphs
- [Obsidian](https://obsidian.md/), [Logseq](https://logseq.com/), [Mem AI](https://get.mem.ai/)
- [Notion 3.0 Agents](https://www.notion.com/releases/2025-09-18)
- [Khoj](https://github.com/khoj-ai/khoj)
- [Screenpipe](https://github.com/mediar-ai/screenpipe)
- [Graphiti](https://github.com/getzep/graphiti)
- [Neo4j LLM Knowledge Graph Builder](https://neo4j.com/blog/developer/llm-knowledge-graph-builder-release/)

### AI Memory Systems
- [Mem0](https://mem0.ai/), [Letta/MemGPT](https://docs.letta.com/), [Zep](https://www.getzep.com/)
- [LangMem](https://github.com/langchain-ai/langmem), [Memobase](https://www.memobase.io/)
- [ChatGPT Memory](https://openai.com/index/memory-and-new-controls-for-chatgpt/)
- [Claude Memory](https://www.anthropic.com/news/memory)
- [A-MEM](https://arxiv.org/abs/2502.12110)

### Data Capture Pipelines
- [ActivityWatch](https://activitywatch.net/)
- [Dogsheep](https://dogsheep.github.io/), [Datasette](https://datasette.io/)
- [Limitless](https://www.limitless.ai/)
- [Granola](https://www.granola.ai/)
- [Obsidian Web Clipper](https://obsidian.md/clipper)
- [Chrome History Embeddings](https://dejan.ai/blog/inside-chromes-semantic-engine-a-technical-analysis-of-history-embeddings/)

---

*Generated 2024-12-24 by Claude (Idle Citizen sandbox activity)*
*Parallel research agents: personal knowledge graphs, AI memory systems, data capture pipelines*
