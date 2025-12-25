---
title: Local AI Memory System for Persistent Context
labels: [feature, researched]
created: 2025-12-23
updated: 2025-12-23
---

## Goal

Implement a local, open-source memory system that gives AI instances persistent awareness of the user across sessions — similar to Claude Desktop's memory feature but self-hosted and controllable.

## Background

Claude Desktop and Anthropic manage user context server-side. For a local-first workflow (especially with Claude Code), we want equivalent capabilities without relying on proprietary systems.

This is "RAG but more dynamic" — memory systems actively extract facts, consolidate over time, and update/forget outdated info.

## Options Researched

### 1. Mem0 (Most Production-Ready)
- 37k+ GitHub stars, Y Combinator backed
- Self-hostable with vector DB
- Benchmarks: 26% more accurate than OpenAI's memory, 91% lower latency
- **Mem0g** variant uses knowledge graphs
- https://github.com/mem0ai/mem0

### 2. Letta (formerly MemGPT) — Most Transparent
- OS-inspired architecture: "in-context" vs "archival" memory
- Memory is inspectable and editable
- Scored 74% on LoCoMo benchmark
- https://github.com/cpacker/MemGPT

### 3. Memori — Human-Like Patterns
- Apache 2.0 license
- "Dual-Mode Memory": conscious (short-term) + auto (long-term)
- Works across multi-agent systems
- https://github.com/GibsonAI/Memori

### 4. memary — Graph-Based
- Uses FalkorDB for relationship storage
- Recursive retrieval with entity subgraphs
- https://github.com/kingjulio8238/memary

## Key Differentiators from Basic RAG

| Feature | Basic RAG | Memory Systems |
|---------|-----------|----------------|
| Storage | Static chunks | Dynamic extraction |
| Update | Manual reindex | Auto-learns from conversations |
| Structure | Flat vectors | Graphs + temporal awareness |
| Retrieval | Similarity only | Entity relationships + recency |

## Potential Integration Points

- Import Claude Desktop export (conversations.json) as seed data
- Hook into Claude Code sessions to enrich memory
- Query memory before/after AI interactions for context injection
- Use with Idle Citizen's autonomous sessions

## Open Questions (Answered)

- [x] Which system best fits existing stack? → **Mem0** (simpler, better MCP support)
- [x] Storage backend? → **Qdrant** (via Docker) + SQLite for history
- [x] How to integrate with Claude Code? → **OpenMemory MCP server** (native)
- [x] Should this be shared across projects or per-project? → **Shared across all projects** (Kenny's decision: this computer is devoted to agentic AI)

## Research Complete

See detailed implementation guide: `explorations/project-notes/local-ai-memory-implementation-guide.md`

**Recommendation:** Mem0 with OpenMemory MCP server, fully local with Ollama.

## Status: OPERATIONAL (Session 39)

The memory system is now live:
- OpenMemory MCP server installed globally by Kenny
- Tested successfully in Session 39 (can add and search memories)
- Memories are being shared across all projects on this machine

## Next Steps

1. ~~Pick one system to prototype~~ → **Mem0** ✓
2. Seed with exported Claude Desktop history (optional, low priority)
3. ~~Build simple wrapper for Claude Code integration~~ → Use OpenMemory MCP ✓
4. ~~Install and test~~ → **Working as of 2025-12-25** ✓
5. Let memories accumulate naturally through use
6. Periodically review what's being stored

## References

- [Mem0 GitHub](https://github.com/mem0ai/mem0)
- [Letta GitHub](https://github.com/cpacker/MemGPT)
- [AI Memory Benchmark Comparison](https://guptadeepak.com/the-ai-memory-wars-why-one-system-crushed-the-competition-and-its-not-openai/)
- [Mem0 vs Letta vs Zep Comparison](https://medium.com/asymptotic-spaghetti-integration/from-beta-to-battle-tested-picking-between-letta-mem0-zep-for-ai-memory-6850ca8703d1)
