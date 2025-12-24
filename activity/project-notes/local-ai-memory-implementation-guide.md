# Local AI Memory System: Implementation Guide

*Deep dive into Mem0 vs Letta for persistent AI context — with a clear recommendation.*

---

## Executive Summary

After researching both systems extensively, **Mem0** is the recommended choice for Kenny's use case. It's simpler to set up, has better MCP integration for Claude Code, supports fully local operation with Ollama, and provides more straightforward APIs.

Letta is more powerful for building autonomous *agents* with complex memory hierarchies, but that's overkill for the goal of giving Claude Code persistent awareness across sessions.

---

## The Core Difference

| Aspect | Mem0 | Letta (MemGPT) |
|--------|------|----------------|
| **Design Philosophy** | Memory as a service — add to any AI | Memory as agent architecture |
| **Primary Use** | Augment existing workflows | Build stateful agents from scratch |
| **Complexity** | Low — `pip install mem0ai` | Medium — requires server + DB |
| **Local-First** | ✅ Full Ollama support | ✅ Docker-based |
| **MCP Integration** | ✅ OpenMemory MCP server | ❌ No native MCP |
| **Claude Code Ready** | ✅ One-liner setup | ⚠️ Requires custom integration |

---

## Mem0: The Recommended Choice

### Why Mem0?

1. **OpenMemory MCP Server** — Native integration with Claude Code via MCP
2. **Simpler Mental Model** — It's "add/search memories" not "manage agent state"
3. **Fully Local** — Ollama for LLM + embeddings, Qdrant for vectors
4. **Production Ready** — 43k+ GitHub stars, Y Combinator backed
5. **Flexible Integration** — Works with any LLM, not just internal agents

### Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                        Claude Code                              │
│                            ↓                                    │
│                     MCP Protocol                                │
│                            ↓                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                 OpenMemory MCP Server                     │  │
│  │  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐ │  │
│  │  │ Mem0 Core   │──│ Ollama LLM   │──│ Ollama Embedder  │ │  │
│  │  │             │  │ (fact extract)│  │ (semantic search)│ │  │
│  │  └─────────────┘  └──────────────┘  └──────────────────┘ │  │
│  │         ↓                                                 │  │
│  │  ┌─────────────┐  ┌──────────────────────────────────┐   │  │
│  │  │ Qdrant      │  │ SQLite History                   │   │  │
│  │  │ (vectors)   │  │ ~/.mem0/history.db               │   │  │
│  │  └─────────────┘  └──────────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

### Quick Start: Mem0 with Claude Code

**Option A: OpenMemory (Docker-based, recommended)**

```bash
# Set your OpenAI key (or configure Ollama later)
export OPENAI_API_KEY="sk-..."

# One-liner install + start
curl -sL https://raw.githubusercontent.com/mem0ai/mem0/main/openmemory/run.sh | bash

# Add to Claude Code
claude mcp add --transport http openmemory http://localhost:8080/mcp
```

Dashboard: http://localhost:3000
MCP Tools available: `openmemory_query`, `openmemory_store`, `openmemory_list`, `openmemory_get`, `openmemory_reinforce`

**Option B: Fully Local with Ollama (no OpenAI)**

```bash
# Install Mem0
pip install mem0ai

# Install Qdrant (vector store)
docker run -p 6333:6333 qdrant/qdrant

# Pull Ollama models
ollama pull mixtral:8x7b          # or llama3.1:8b for LLM
ollama pull nomic-embed-text      # for embeddings
```

Python config:

```python
from mem0 import Memory

config = {
    "llm": {
        "provider": "ollama",
        "config": {
            "model": "mixtral:8x7b",
            "temperature": 0.1,
            "max_tokens": 2000,
        }
    },
    "embedder": {
        "provider": "ollama",
        "config": {
            "model": "nomic-embed-text",
            "embedding_dims": 768,
        }
    },
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "host": "localhost",
            "port": 6333,
        }
    }
}

memory = Memory.from_config(config)
```

### Basic Usage Pattern

```python
from mem0 import Memory

memory = Memory()  # or Memory.from_config(config)

# Store memories from a conversation
messages = [
    {"role": "user", "content": "I prefer TypeScript over JavaScript"},
    {"role": "assistant", "content": "Got it, I'll use TypeScript in examples."},
    {"role": "user", "content": "My main project is called Tho, it's an Electron app"},
]
memory.add(messages, user_id="kenny")

# Later, retrieve relevant context
results = memory.search("What tech stack does the user prefer?", user_id="kenny")
# Returns: memories about TypeScript preference, Electron, Tho project
```

### MCP Server for Claude Code

For a custom MCP integration (beyond OpenMemory), use the community server:

**~/.claude/mcp.json**:
```json
{
  "mcpServers": {
    "mem0": {
      "command": "python3",
      "args": ["/path/to/mem0_stdio_mcp.py"],
      "env": {
        "MEM0_ANTHROPIC_KEY": "your-key"
      }
    }
  }
}
```

This gives Claude Code tools to:
- Store facts from conversations
- Retrieve relevant context before responding
- Update/delete outdated information

---

## Letta: When You Actually Need It

Letta is the right choice if you're building **autonomous agents** that need:

- Self-modifying memory (agent decides what to remember)
- Tiered memory (core/archival/recall)
- Multi-agent coordination
- Agent observability and debugging UI

### Memory Model

```
                    Context Window
┌──────────────────────────────────────────────────────┐
│  ┌────────────────────────────────────────────────┐  │
│  │           Core Memory (Always Present)         │  │
│  │  ┌─────────────────┐  ┌─────────────────────┐ │  │
│  │  │ Human Block     │  │ Persona Block       │ │  │
│  │  │ (user info)     │  │ (agent personality) │ │  │
│  │  └─────────────────┘  └─────────────────────┘ │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│  ┌────────────────────────────────────────────────┐  │
│  │         Working Memory (Conversation)          │  │
│  │  [msg1] [msg2] [msg3] ... [msgN]              │  │
│  │  ↓ summarized when full ↓                     │  │
│  └────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘
                         ↕ agent-controlled tools
     ┌─────────────────────────────────────────────┐
     │          External Storage                   │
     │  ┌─────────────────┐  ┌──────────────────┐ │
     │  │ Archival Memory │  │ Recall Memory    │ │
     │  │ (vector DB)     │  │ (conversation    │ │
     │  │ long-term facts │  │  history search) │ │
     │  └─────────────────┘  └──────────────────┘ │
     └─────────────────────────────────────────────┘
```

### Setup (Docker)

```bash
docker run \
  -v ~/.letta/.persist/pgdata:/var/lib/postgresql/data \
  -p 8283:8283 \
  -e OPENAI_API_KEY="your_key" \
  letta/letta:latest
```

Access ADE (Agent Development Environment): http://localhost:8283

### Python SDK

```python
from letta_client import Letta

client = Letta(base_url="http://localhost:8283")

# Create agent with memory blocks
agent = client.agents.create(
    name="my-assistant",
    model="gpt-4o-mini",
    memory_blocks=[
        {"label": "human", "value": "User preferences go here"},
        {"label": "persona", "value": "I am a helpful coding assistant"},
    ]
)

# Send message — agent manages its own memory
response = client.agents.messages.create(
    agent_id=agent.id,
    messages=[{"role": "user", "content": "I prefer Python over JavaScript"}]
)
# Agent automatically updates its memory blocks based on the conversation
```

---

## Benchmark Reality Check

Both projects claim to outperform each other on LoCoMo. The truth:

- **Mem0** claims: 26% more accurate than OpenAI, 91% lower latency
- **Letta** claims: Simple filesystem achieves 74% vs Mem0's 68.5%

The real insight from Letta's research: *agent quality matters more than memory system*. A well-designed agent with basic file tools can outperform a mediocre agent with sophisticated memory infrastructure.

**Takeaway:** Pick based on ergonomics and use case, not benchmarks.

---

## Recommendation Summary

| Use Case | Recommendation |
|----------|----------------|
| Add memory to Claude Code | **Mem0** (OpenMemory MCP) |
| Build autonomous agents | **Letta** |
| Quick local prototype | **Mem0** (pip install + Ollama) |
| Complex multi-agent system | **Letta** |
| Integrate with existing app | **Mem0** |
| Need inspectable agent state | **Letta** (ADE dashboard) |

---

## Implementation Plan for Kenny

### Phase 1: Quick Win (1 session)

1. Install OpenMemory via Docker
2. Configure Claude Code MCP integration
3. Test basic store/retrieve flow

### Phase 2: Seed with History

1. Export Claude Desktop conversations (if available)
2. Parse and feed into Mem0
3. Verify retrieval quality

### Phase 3: Go Fully Local

1. Replace OpenAI with Ollama for LLM
2. Replace OpenAI embeddings with Ollama embedder
3. Keep Qdrant for vector storage
4. Remove all external API dependencies

### Phase 4: Cross-Project Memory

1. Configure user_id-based isolation
2. Decide: shared vs per-project memory
3. Add to Idle Citizen for autonomous sessions

---

## Resources

- [Mem0 GitHub](https://github.com/mem0ai/mem0)
- [Mem0 Docs](https://docs.mem0.ai/)
- [OpenMemory MCP Setup](https://docs.mem0.ai/openmemory/overview)
- [Letta GitHub](https://github.com/letta-ai/letta)
- [Letta Docs](https://docs.letta.com/)
- [Mem0 + Claude Integration Tutorial](https://www.marktechpost.com/2025/05/10/a-coding-guide-to-unlock-mem0-memory-for-anthropic-claude-bot-enabling-context-rich-conversations/)
- [LoCoMo Benchmark](https://www.letta.com/blog/benchmarking-ai-agent-memory)
- [Mem0 vs Letta Comparison](https://openalternative.co/compare/letta/vs/mem0)

---

*Generated: 2025-12-23 | Session 11 | Project Helper Mode*
