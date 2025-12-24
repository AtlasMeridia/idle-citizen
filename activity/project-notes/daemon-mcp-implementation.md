# DAEMON MCP Implementation Guide

**Created:** 2025-12-24
**Purpose:** Implementation guide for Model Context Protocol (MCP) integration in DAEMON
**Status:** Research complete, ready for implementation

---

## Executive Summary

MCP (Model Context Protocol) is the standardized way for DAEMON to interact with external tools and data sources. This guide covers how to integrate MCP into DAEMON's orchestrator, which pre-built servers to leverage, and how to create custom servers for DAEMON-specific functionality.

**Key Recommendation:** Use the official MCP Python SDK with FastMCP patterns for server creation. For the MCP client layer, use one of the Ollama-compatible MCP clients (mcp-client-for-ollama) or build a lightweight custom client.

---

## 1. What is MCP?

Model Context Protocol is an open standard introduced by Anthropic (November 2024) for connecting AI systems to tools and data sources. In December 2025, it was donated to the Linux Foundation, with adoption from OpenAI, Google, Microsoft, and AWS.

### MCP Architecture

```
┌─────────────────┐
│   LLM Client    │ ← DAEMON's orchestrator (with tool-calling LLM)
│  (MCP Client)   │
└────────┬────────┘
         │ JSON-RPC 2.0
         │ (stdio or HTTP/SSE)
         ▼
┌─────────────────┐
│   MCP Server    │ ← Exposes tools, resources, prompts
│ (e.g., Memory)  │
└─────────────────┘
```

### Three Capability Types

| Type | Purpose | Analogy |
|------|---------|---------|
| **Resources** | Expose data to read | GET endpoints |
| **Tools** | Execute actions/functions | POST endpoints |
| **Prompts** | Reusable LLM prompt templates | Templates |

---

## 2. MCP for DAEMON's Architecture

DAEMON's intent doc specifies a modular architecture with hot-swappable modules. MCP fits perfectly:

### Current Module → MCP Integration Plan

| DAEMON Module | MCP Approach |
|---------------|--------------|
| Memory Store | Use `@modelcontextprotocol/server-memory` (knowledge graph) or Mem0's OpenMemory MCP server |
| File System | Use `@modelcontextprotocol/server-filesystem` with scoped access |
| Web Search | Use Brave Search MCP server (privacy-focused, free tier) |
| Code Execution | Custom sandboxed MCP server |
| R&D Agent | Custom MCP server wrapping researchscan |
| Personality Config | Custom MCP resource for loading/saving config |

### Integration Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    DAEMON ORCHESTRATOR                        │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              MCP Client Layer                           │  │
│  │  • Connects to multiple MCP servers                     │  │
│  │  • Manages tool discovery and invocation                │  │
│  │  • Formats results for LLM consumption                  │  │
│  └──────────────────────────┬─────────────────────────────┘  │
└─────────────────────────────┼────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  Memory Server  │  │ Filesystem Srv  │  │ Brave Search    │
│  (Mem0 MCP)     │  │ (Official)      │  │  Server         │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

---

## 3. Pre-Built MCP Servers to Use

### Official Reference Servers (Recommended)

These are maintained by Anthropic/MCP organization:

#### Memory Server
```bash
npx -y @modelcontextprotocol/server-memory
```
- Knowledge-graph based persistent memory
- Good for episodic/semantic memory
- Consider: May replace or complement Mem0

#### Filesystem Server
```bash
npx -y @modelcontextprotocol/server-filesystem /path/to/allowed/files
```
- Secure file operations with configurable access
- Scoped to specified directories
- Supports: read, write, list, search

#### Fetch Server
```bash
npx -y @modelcontextprotocol/server-fetch
```
- Web content fetching and conversion
- Optimized for LLM consumption (markdown output)

#### Git Server
```bash
npx -y @modelcontextprotocol/server-git /path/to/repo
```
- Read, search, and analyze git repositories
- Useful for code-aware conversations

### Third-Party Servers

#### Brave Search
- Privacy-focused web search
- Free tier: 2,000 queries/month
- Requires API key from Brave
- Installation: `npm install @anthropic-ai/mcp-server-brave-search`

#### Mem0 OpenMemory (For DAEMON's Memory)
- Already researched in session 11
- Native MCP integration
- Better for long-term memory management than the reference memory server
- Works with Ollama for local embeddings

---

## 4. MCP Client Implementation for DAEMON

Since DAEMON uses local LLMs (Ollama), you need an MCP client that works with Ollama's tool-calling API.

### Option A: Use mcp-client-for-ollama (Recommended for Testing)

```bash
# Install
git clone https://github.com/jonigl/mcp-client-for-ollama.git
cd mcp-client-for-ollama
uv venv && source .venv/bin/activate
uv pip install .

# Run
ollmcp
```

Features:
- TUI interface for testing
- Multi-server support
- Dynamic model switching
- Configuration persistence

### Option B: Build Custom MCP Client (Recommended for Production)

For DAEMON's thin-shell principle, build a lightweight MCP client layer:

```python
"""
DAEMON MCP Client Layer
Connects to MCP servers and exposes tools to the orchestrator.
"""

import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class DAEMONMCPClient:
    """Manages connections to multiple MCP servers."""

    def __init__(self):
        self.sessions: dict[str, ClientSession] = {}
        self.tools: dict[str, dict] = {}

    async def connect_server(
        self,
        name: str,
        command: str,
        args: list[str] = None
    ):
        """Connect to an MCP server via stdio."""
        server_params = StdioServerParameters(
            command=command,
            args=args or []
        )

        stdio, write = await stdio_client(server_params)
        session = ClientSession(stdio, write)
        await session.initialize()

        # Discover tools
        tools_response = await session.list_tools()
        for tool in tools_response.tools:
            self.tools[f"{name}:{tool.name}"] = {
                "description": tool.description,
                "schema": tool.inputSchema,
                "session": session
            }

        self.sessions[name] = session
        return tools_response.tools

    async def call_tool(self, tool_name: str, arguments: dict) -> str:
        """Call a tool by its namespaced name."""
        if tool_name not in self.tools:
            raise ValueError(f"Unknown tool: {tool_name}")

        tool_info = self.tools[tool_name]
        _, actual_name = tool_name.split(":", 1)

        result = await tool_info["session"].call_tool(actual_name, arguments)
        return result.content

    def get_tool_schemas(self) -> list[dict]:
        """Get all tool schemas in Ollama/OpenAI function format."""
        schemas = []
        for name, info in self.tools.items():
            schemas.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": info["description"],
                    "parameters": info["schema"]
                }
            })
        return schemas

    async def close_all(self):
        """Close all server connections."""
        for session in self.sessions.values():
            await session.close()


# Usage in DAEMON orchestrator
async def main():
    client = DAEMONMCPClient()

    # Connect to servers
    await client.connect_server(
        "memory",
        "npx",
        ["-y", "@modelcontextprotocol/server-memory"]
    )
    await client.connect_server(
        "fs",
        "npx",
        ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/documents"]
    )

    # Get tools for LLM
    tools = client.get_tool_schemas()

    # Use with Ollama
    # response = ollama.chat(model="qwen2.5:72b", tools=tools, messages=[...])
    # tool_calls = response.message.tool_calls
    # for call in tool_calls:
    #     result = await client.call_tool(call.function.name, call.function.arguments)
```

---

## 5. Creating Custom MCP Servers for DAEMON

For DAEMON-specific functionality, create custom MCP servers using the Python SDK.

### Installation

```bash
uv add mcp
# Or: pip install mcp
```

### Example: DAEMON Personality Server

```python
"""
DAEMON Personality MCP Server
Exposes personality configuration as resources and tools.
"""

from mcp.server.fastmcp import FastMCP
import yaml
from pathlib import Path

mcp = FastMCP("daemon-personality")

PERSONALITY_DIR = Path("~/.daemon/personalities").expanduser()

# Resource: Read current personality
@mcp.resource("personality://current")
def get_current_personality() -> str:
    """Get the currently active personality configuration."""
    active_link = PERSONALITY_DIR / "active.yaml"
    if not active_link.exists():
        return "No active personality configured"
    return active_link.read_text()

# Resource: List available personalities
@mcp.resource("personality://available")
def list_personalities() -> str:
    """List all available personality configurations."""
    personalities = []
    for f in PERSONALITY_DIR.glob("*.yaml"):
        if f.name != "active.yaml":
            personalities.append(f.stem)
    return "\n".join(personalities) or "No personalities found"

# Tool: Switch personality
@mcp.tool()
def switch_personality(name: str) -> str:
    """Switch to a different personality configuration.

    Args:
        name: Name of the personality to activate
    """
    personality_file = PERSONALITY_DIR / f"{name}.yaml"
    if not personality_file.exists():
        return f"Personality '{name}' not found"

    active_link = PERSONALITY_DIR / "active.yaml"
    active_link.unlink(missing_ok=True)
    active_link.symlink_to(personality_file)

    return f"Switched to personality: {name}"

# Tool: Update personality parameter
@mcp.tool()
def update_personality_param(param: str, value: str) -> str:
    """Update a specific personality parameter.

    Args:
        param: Parameter path (e.g., 'voice.formality')
        value: New value for the parameter
    """
    active_file = PERSONALITY_DIR / "active.yaml"
    if not active_file.exists():
        return "No active personality"

    config = yaml.safe_load(active_file.read_text())

    # Navigate to param
    keys = param.split(".")
    target = config
    for key in keys[:-1]:
        target = target.setdefault(key, {})
    target[keys[-1]] = value

    # Save and version
    active_file.write_text(yaml.dump(config))
    return f"Updated {param} to {value}"

if __name__ == "__main__":
    mcp.run()
```

### Example: R&D Agent Server (wrapping researchscan)

```python
"""
DAEMON R&D Agent MCP Server
Exposes research scanning as tools.
"""

from mcp.server.fastmcp import FastMCP
import subprocess
import json

mcp = FastMCP("daemon-rnd")

RESEARCHSCAN_PATH = "~/.local/bin/researchscan"

@mcp.tool()
def get_new_papers(days: int = 1) -> str:
    """Get new AI research papers since last check.

    Args:
        days: Number of days to look back (default: 1)
    """
    result = subprocess.run(
        [RESEARCHSCAN_PATH, "new", "--days", str(days), "--json"],
        capture_output=True,
        text=True
    )
    return result.stdout

@mcp.tool()
def search_papers(query: str, limit: int = 10) -> str:
    """Search research papers by keyword.

    Args:
        query: Search query
        limit: Maximum results (default: 10)
    """
    result = subprocess.run(
        [RESEARCHSCAN_PATH, "search", query, "--limit", str(limit), "--json"],
        capture_output=True,
        text=True
    )
    return result.stdout

@mcp.tool()
def refresh_sources() -> str:
    """Refresh papers from arXiv and HuggingFace."""
    result = subprocess.run(
        [RESEARCHSCAN_PATH, "refresh"],
        capture_output=True,
        text=True
    )
    return f"Refreshed: {result.stdout}"

@mcp.resource("rnd://trending")
def get_trending() -> str:
    """Get currently trending models from HuggingFace."""
    result = subprocess.run(
        [RESEARCHSCAN_PATH, "trending", "--json"],
        capture_output=True,
        text=True
    )
    return result.stdout

if __name__ == "__main__":
    mcp.run()
```

---

## 6. Server Configuration

MCP servers are typically configured in a JSON file. For DAEMON, create `~/.daemon/mcp-servers.json`:

```json
{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"]
    },
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/Users/kenny/Documents",
        "/Users/kenny/Projects"
      ]
    },
    "fetch": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-fetch"]
    },
    "brave-search": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/mcp-server-brave-search"],
      "env": {
        "BRAVE_API_KEY": "${BRAVE_API_KEY}"
      }
    },
    "daemon-personality": {
      "command": "python",
      "args": ["/path/to/daemon/mcp/personality_server.py"]
    },
    "daemon-rnd": {
      "command": "python",
      "args": ["/path/to/daemon/mcp/rnd_server.py"]
    }
  }
}
```

---

## 7. Integration with DAEMON's Orchestrator

The orchestrator loop with MCP:

```python
"""
DAEMON Orchestrator with MCP Integration
"""

import asyncio
import ollama
from daemon.mcp_client import DAEMONMCPClient
from daemon.memory import load_context
from daemon.personality import load_personality

async def orchestrator_loop():
    # 1. Initialize MCP client and connect to servers
    mcp = DAEMONMCPClient()
    await mcp.load_from_config("~/.daemon/mcp-servers.json")

    # 2. Get available tools
    tools = mcp.get_tool_schemas()

    # 3. Load personality and context
    personality = load_personality()
    context = load_context()

    while True:
        # 4. Get user input (voice or text)
        user_input = await get_input()

        # 5. Build message with context
        messages = [
            {"role": "system", "content": personality.to_prompt()},
            *context.recent_messages(),
            {"role": "user", "content": user_input}
        ]

        # 6. Call LLM with tools
        response = ollama.chat(
            model="qwen2.5:72b",
            messages=messages,
            tools=tools
        )

        # 7. Process tool calls if any
        while response.message.tool_calls:
            for call in response.message.tool_calls:
                result = await mcp.call_tool(
                    call.function.name,
                    call.function.arguments
                )
                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": result
                })

            # Continue conversation with tool results
            response = ollama.chat(
                model="qwen2.5:72b",
                messages=messages,
                tools=tools
            )

        # 8. Output response
        await output_response(response.message.content)

        # 9. Update memory
        await mcp.call_tool("memory:add_memory", {
            "content": f"User: {user_input}\nDAEMON: {response.message.content}"
        })
```

---

## 8. Transport Options

MCP supports two transports:

### stdio (Recommended for local)
- Server runs as subprocess
- Communication via stdin/stdout
- Simple, no network setup
- Best for local DAEMON deployment

### HTTP with SSE (For remote/distributed)
- Server runs as web service
- Supports multiple clients
- Better for networked deployments
- Requires FastAPI/Starlette setup

For DAEMON Phase 1, use **stdio** for simplicity.

---

## 9. Implementation Roadmap

### Week 1: Core MCP Client
1. Install MCP Python SDK
2. Implement `DAEMONMCPClient` class
3. Test with official Memory and Filesystem servers
4. Verify tool discovery and invocation

### Week 2: Server Configuration
1. Create `mcp-servers.json` config
2. Implement config loader in client
3. Test multi-server connections
4. Add connection health monitoring

### Week 3: Custom Servers
1. Create personality MCP server
2. Create R&D agent MCP server
3. Integrate with researchscan
4. Test end-to-end

### Week 4: Orchestrator Integration
1. Wire MCP into orchestrator loop
2. Implement tool result formatting
3. Add memory persistence via MCP
4. Full integration test

---

## 10. Resources

### Official Documentation
- [MCP Specification](https://modelcontextprotocol.io)
- [Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Server Examples](https://modelcontextprotocol.io/examples)

### Reference Servers
- [Official Servers Repo](https://github.com/modelcontextprotocol/servers)
- [MCP Registry](https://registry.modelcontextprotocol.io)

### Ollama Integration
- [mcp-client-for-ollama](https://github.com/jonigl/mcp-client-for-ollama)
- [ollama-mcp-client](https://github.com/mihirrd/ollama-mcp-client)
- [MCP-ollama_server](https://github.com/Sethuram2003/MCP-ollama_server)

### Tutorials
- [Building MCP Server in Python](https://medium.com/data-engineering-with-dremio/building-a-basic-mcp-server-with-python-4c34c41031ed)
- [MCP with Ollama Guide](https://medium.com/data-science-in-your-pocket/model-context-protocol-mcp-using-ollama-e719b2d9fd7a)
- [DataCamp MCP Tutorial](https://www.datacamp.com/tutorial/mcp-model-context-protocol)

---

## Summary

MCP provides the standardized tool interface DAEMON needs. Key takeaways:

1. **Use official servers** for filesystem, fetch, git, and memory
2. **Build custom servers** for DAEMON-specific features (personality, R&D)
3. **Use stdio transport** for Phase 1 simplicity
4. **The MCP Python SDK** with FastMCP patterns makes server creation easy
5. **For Ollama integration**, build a lightweight MCP client or use mcp-client-for-ollama

This completes the research on DAEMON's tool layer, complementing existing guides on LLM selection, TTS, STT, VLM, memory, and personality configuration.
