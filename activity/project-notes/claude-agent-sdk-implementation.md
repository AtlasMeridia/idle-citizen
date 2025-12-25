# Claude Agent SDK Implementation Guide

*Building autonomous agents using the same infrastructure as Claude Code. Directly relevant to DAEMON development.*

---

## Overview

The Claude Agent SDK (formerly Claude Code SDK) provides the building blocks for production-ready AI agents. It exposes the same tools, agent loop, and context management that power Claude Code as a programmable library.

**Key insight:** This is not just an API wrapper. It includes built-in tool execution — Claude can read files, run commands, and edit code without you implementing the execution layer.

---

## Why This Matters for DAEMON

The DAEMON architecture (documented in 12 prior guides) envisions a local AI companion with:
- Voice interface
- Persistent memory (Mem0)
- Tool access (MCP)
- Orchestration layer

The Agent SDK provides:
- **Pre-built tools** — File ops, bash, web search already implemented
- **MCP integration** — Native support for Model Context Protocol
- **Subagents** — Spawn specialized agents for focused tasks
- **Context management** — Automatic compaction, session resumption
- **Hooks** — Intercept and modify agent behavior at key points

This aligns with DAEMON's modular, orchestrator-driven design.

---

## Installation

### Prerequisites
- Python 3.10+ or Node.js
- Anthropic API key

### Python

```bash
pip install claude-agent-sdk
```

The Claude Code CLI is bundled automatically — no separate installation needed.

### TypeScript

```bash
npm install @anthropic-ai/claude-agent-sdk
```

### API Key

```bash
export ANTHROPIC_API_KEY=your-api-key
```

Alternative providers supported:
- **Amazon Bedrock:** `CLAUDE_CODE_USE_BEDROCK=1`
- **Google Vertex AI:** `CLAUDE_CODE_USE_VERTEX=1`

---

## Core Concepts

### The Agent Loop

Agents operate in a feedback cycle: **gather context → take action → verify work → repeat**

This is the same loop DAEMON's orchestrator would implement, but the SDK handles it natively.

### Two APIs

| API | Use Case |
|-----|----------|
| `query()` | Simple async queries, streaming responses |
| `ClaudeSDKClient` | Bidirectional conversations, custom tools, hooks |

---

## Basic Usage

### Simple Query

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions

async def main():
    async for message in query(
        prompt="Find all TODO comments in this codebase",
        options=ClaudeAgentOptions(allowed_tools=["Read", "Glob", "Grep"])
    ):
        if hasattr(message, "result"):
            print(message.result)

asyncio.run(main())
```

### With Options

```python
options = ClaudeAgentOptions(
    allowed_tools=["Read", "Edit", "Bash"],
    permission_mode="acceptEdits",  # Auto-accept file edits
    system_prompt="You are a helpful coding assistant",
    cwd="/path/to/project",
    max_turns=10
)
```

---

## Built-in Tools

These work immediately without implementation:

| Tool | Description |
|------|-------------|
| **Read** | Read any file in working directory |
| **Write** | Create new files |
| **Edit** | Precise edits to existing files |
| **Bash** | Terminal commands, scripts, git |
| **Glob** | Find files by pattern (`**/*.py`) |
| **Grep** | Search file contents with regex |
| **WebSearch** | Search the web |
| **WebFetch** | Fetch and parse web pages |
| **Task** | Spawn subagents |

---

## Custom Tools

### In-Process MCP Servers

The SDK supports custom tools as Python functions, running in-process (no subprocesses):

```python
from claude_agent_sdk import tool, create_sdk_mcp_server, ClaudeAgentOptions, ClaudeSDKClient

@tool("get_weather", "Get current weather", {"city": str})
async def get_weather(args):
    city = args["city"]
    # Actual implementation here
    return {
        "content": [
            {"type": "text", "text": f"Weather in {city}: Sunny, 72°F"}
        ]
    }

@tool("send_message", "Send a message to user", {"text": str})
async def send_message(args):
    # Could integrate with TTS for DAEMON
    print(f"[DAEMON says]: {args['text']}")
    return {"content": [{"type": "text", "text": "Message sent"}]}

# Create server
server = create_sdk_mcp_server(
    name="daemon-tools",
    version="1.0.0",
    tools=[get_weather, send_message]
)

# Use with agent
options = ClaudeAgentOptions(
    mcp_servers={"daemon": server},
    allowed_tools=["mcp__daemon__get_weather", "mcp__daemon__send_message"]
)

async with ClaudeSDKClient(options=options) as client:
    await client.query("What's the weather in San Francisco?")
    async for msg in client.receive_response():
        print(msg)
```

### Benefits of In-Process Tools

- No subprocess management
- Better performance (no IPC overhead)
- Easier debugging
- Type safety with Python functions

### External MCP Servers

For pre-built servers (Playwright, databases, etc.):

```python
options = ClaudeAgentOptions(
    mcp_servers={
        "playwright": {"command": "npx", "args": ["@playwright/mcp@latest"]}
    }
)
```

---

## Subagents

Spawn specialized agents for focused tasks:

```python
from claude_agent_sdk import query, ClaudeAgentOptions, AgentDefinition

options = ClaudeAgentOptions(
    allowed_tools=["Read", "Glob", "Grep", "Task"],  # Task enables subagents
    agents={
        "researcher": AgentDefinition(
            description="Expert researcher for finding information",
            prompt="Search thoroughly, cite sources, synthesize findings",
            tools=["Read", "Glob", "Grep", "WebSearch", "WebFetch"]
        ),
        "code-reviewer": AgentDefinition(
            description="Code quality and security reviewer",
            prompt="Analyze for best practices, security issues, performance",
            tools=["Read", "Glob", "Grep"]
        )
    }
)

async for message in query(
    prompt="Use the researcher to find information about X",
    options=options
):
    if hasattr(message, "result"):
        print(message.result)
```

---

## Hooks

Intercept agent behavior at key points:

### Available Hook Points

- `PreToolUse` — Before tool execution
- `PostToolUse` — After tool execution
- `Stop` — When agent stops
- `SessionStart` / `SessionEnd`
- `UserPromptSubmit`

### Example: Audit Logging

```python
from datetime import datetime
from claude_agent_sdk import query, ClaudeAgentOptions, HookMatcher

async def log_file_change(input_data, tool_use_id, context):
    file_path = input_data.get('tool_input', {}).get('file_path', 'unknown')
    with open('./audit.log', 'a') as f:
        f.write(f"{datetime.now()}: modified {file_path}\n")
    return {}

options = ClaudeAgentOptions(
    permission_mode="acceptEdits",
    hooks={
        "PostToolUse": [
            HookMatcher(matcher="Edit|Write", hooks=[log_file_change])
        ]
    }
)
```

### Example: Command Validation

```python
async def validate_bash_command(input_data, tool_use_id, context):
    if input_data["tool_name"] != "Bash":
        return {}

    command = input_data["tool_input"].get("command", "")
    forbidden = ["rm -rf", "sudo", "curl | sh"]

    for pattern in forbidden:
        if pattern in command:
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"Command contains '{pattern}'"
                }
            }
    return {}

options = ClaudeAgentOptions(
    hooks={
        "PreToolUse": [
            HookMatcher(matcher="Bash", hooks=[validate_bash_command])
        ]
    }
)
```

---

## Sessions

Maintain context across multiple exchanges:

```python
async def main():
    session_id = None

    # First query — capture session ID
    async for message in query(
        prompt="Read the authentication module",
        options=ClaudeAgentOptions(allowed_tools=["Read", "Glob"])
    ):
        if hasattr(message, 'subtype') and message.subtype == 'init':
            session_id = message.session_id

    # Resume with full context
    async for message in query(
        prompt="Now find all places that call it",
        options=ClaudeAgentOptions(resume=session_id)
    ):
        if hasattr(message, "result"):
            print(message.result)
```

---

## DAEMON Integration Pattern

Here's how the Agent SDK maps to DAEMON's architecture:

### DAEMON Orchestrator as Agent SDK Client

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, tool, create_sdk_mcp_server

# DAEMON tools as in-process MCP server
@tool("speak", "Speak text aloud via TTS", {"text": str})
async def speak(args):
    # Call Kokoro TTS
    audio = tts_engine.synthesize(args["text"])
    audio_player.play(audio)
    return {"content": [{"type": "text", "text": "Spoken"}]}

@tool("remember", "Store a memory", {"content": str, "category": str})
async def remember(args):
    # Store in Mem0
    mem0_client.add(args["content"], metadata={"category": args["category"]})
    return {"content": [{"type": "text", "text": "Remembered"}]}

@tool("recall", "Search memories", {"query": str})
async def recall(args):
    memories = mem0_client.search(args["query"])
    return {"content": [{"type": "text", "text": str(memories)}]}

daemon_tools = create_sdk_mcp_server(
    name="daemon",
    version="1.0.0",
    tools=[speak, remember, recall]
)

# DAEMON orchestrator
class DAEMONOrchestrator:
    def __init__(self, personality_config):
        self.options = ClaudeAgentOptions(
            system_prompt=self.build_system_prompt(personality_config),
            mcp_servers={"daemon": daemon_tools},
            allowed_tools=[
                "mcp__daemon__speak",
                "mcp__daemon__remember",
                "mcp__daemon__recall",
                "Read", "Glob", "Grep", "WebSearch"
            ],
            hooks={
                "PreToolUse": [HookMatcher(matcher=".*", hooks=[self.log_action])],
            }
        )

    async def process(self, user_input):
        async with ClaudeSDKClient(options=self.options) as client:
            await client.query(user_input)
            async for msg in client.receive_response():
                yield msg

    async def log_action(self, input_data, tool_use_id, context):
        # Intent tracking per DAEMON guide
        self.log_intent(input_data)
        return {}
```

### Key Integration Points

1. **Memory** — Custom MCP tools wrapping Mem0
2. **Voice** — TTS tool for speech synthesis
3. **Personality** — System prompt from config
4. **Intent Tracking** — Hooks for logging user goals
5. **File Access** — Built-in Read/Glob/Grep tools
6. **Web Research** — Built-in WebSearch/WebFetch

---

## Error Handling

```python
from claude_agent_sdk import (
    ClaudeSDKError,      # Base error
    CLINotFoundError,    # Claude Code not installed
    CLIConnectionError,  # Connection issues
    ProcessError,        # Process failed
    CLIJSONDecodeError,  # JSON parsing issues
)

try:
    async for message in query(prompt="Hello"):
        pass
except CLINotFoundError:
    print("Please install Claude Code")
except ProcessError as e:
    print(f"Process failed with exit code: {e.exit_code}")
except ClaudeSDKError as e:
    print(f"SDK error: {e}")
```

---

## Best Practices

### From Anthropic's Engineering Blog

1. **Tools over prompts** — Grant agents computer access (terminal, files, search) rather than complex prompting
2. **Folder structure is context engineering** — Organize files so search finds relevant info
3. **Use subagents for parallelization** — Multiple focused agents working simultaneously
4. **Compaction handles context limits** — SDK automatically summarizes as context fills
5. **Visual feedback for UI work** — Screenshots validate generated interfaces
6. **Rules-based verification** — Linting, type checking for automatic feedback

### Improvement Checklist

| Problem | Solution |
|---------|----------|
| Missing information | Restructure search for discoverability |
| Repeated failures | Add formal rules to identify issues |
| Can't self-correct | Provide alternative tools |
| Performance variance | Build test sets for evaluation |

---

## Resources

- [Agent SDK Overview](https://platform.claude.com/docs/en/api/agent-sdk/overview) — Official docs
- [Building Agents with the Claude Agent SDK](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk) — Anthropic engineering blog
- [Python SDK GitHub](https://github.com/anthropics/claude-agent-sdk-python) — 3.7k stars
- [TypeScript SDK GitHub](https://github.com/anthropics/claude-agent-sdk-typescript)
- [Example Agents](https://github.com/anthropics/claude-agent-sdk-demos) — Email assistant, research agent, etc.

---

## Next Steps for DAEMON

With the Agent SDK:

1. **Replace orchestrator loop** — SDK's agent loop handles context, tools, subagents
2. **Implement DAEMON tools as in-process MCP** — Memory, TTS, intent tracking
3. **Use hooks for intent logging** — PreToolUse/PostToolUse for goal tracking
4. **Session resumption for continuity** — Maintain conversation context across interactions
5. **Subagents for R&D scanning** — Parallel research across arXiv, HuggingFace, etc.

The Agent SDK essentially provides the "orchestrator" and "tool execution" layers from the DAEMON architecture, leaving you to focus on:
- Memory integration (Mem0 custom tool)
- Voice I/O (TTS/STT custom tools)
- Personality configuration (system prompt)
- Interface (Tauri frontend)

---

*Created: 2025-12-24 (Session 37)*
