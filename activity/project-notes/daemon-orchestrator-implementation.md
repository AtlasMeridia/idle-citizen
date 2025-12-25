# DAEMON Orchestrator Implementation Guide

**Created:** 2025-12-25 (Session 33)
**Purpose:** Implementation guide for DAEMON's core orchestration layer

---

## Overview

The orchestrator is the central nervous system of DAEMON—the thin shell that coordinates all modules while owning the durable parts (memory, personality, state). It implements the "thin shell principle": minimal custom infrastructure, maximum leverage of improving components.

This guide covers:
1. Architecture and responsibilities
2. Conversation loop design
3. Memory integration patterns
4. Tool/module routing
5. State management
6. Python implementation

---

## I. Architecture

### What the Orchestrator Owns

```
┌────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR                         │
│                                                         │
│  ┌─────────────────┐  ┌─────────────────────────────┐  │
│  │ Conversation    │  │ Memory Manager              │  │
│  │ State           │  │ • Read/write to stores      │  │
│  │ • Current turn  │  │ • Relevance filtering       │  │
│  │ • Active intent │  │ • Consolidation triggers    │  │
│  │ • Tool context  │  └─────────────────────────────┘  │
│  └─────────────────┘                                    │
│                                                         │
│  ┌─────────────────┐  ┌─────────────────────────────┐  │
│  │ Personality     │  │ Module Registry             │  │
│  │ Config          │  │ • Available tools           │  │
│  │ • Loaded at     │  │ • Health status             │  │
│  │   startup       │  │ • Capability routing        │  │
│  │ • Injected into │  └─────────────────────────────┘  │
│  │   prompts       │                                    │
│  └─────────────────┘                                    │
└────────────────────────────────────────────────────────┘
          │
          ▼
   Delegates to modules for:
   • LLM inference (Ollama/MLX)
   • Speech I/O (Whisper, Kokoro)
   • Vision (Qwen-VL)
   • Tools (MCP servers)
```

### What the Orchestrator Does NOT Own

- **Intelligence**: Delegates to LLM module
- **Perception**: Delegates to speech/vision modules
- **Actions**: Delegates to tool modules via MCP
- **Storage mechanics**: Uses external stores (Qdrant, SQLite)

This separation means model upgrades, new tools, or backend changes don't require orchestrator rewrites.

---

## II. The Conversation Loop

### Basic Flow

```python
async def conversation_loop():
    while True:
        # 1. Get input (text, voice, or event)
        user_input = await get_input()

        # 2. Build context
        context = await build_context(user_input)

        # 3. Generate response (may involve tool calls)
        response = await generate_with_tools(context)

        # 4. Update memory
        await update_memory(user_input, response)

        # 5. Output response
        await output_response(response)
```

### Context Building

Context is the orchestrator's primary job. For each turn, assemble:

```python
@dataclass
class ConversationContext:
    # Immediate
    user_input: str
    conversation_history: list[Message]  # Recent turns

    # Retrieved
    relevant_memories: list[Memory]      # From semantic search
    active_project: Optional[Project]    # If working on something

    # Configuration
    personality: PersonalityConfig
    available_tools: list[ToolDefinition]

    # Meta
    timestamp: datetime
    session_id: str
```

### The Generate-with-Tools Loop

DAEMON uses tool-augmented generation. The orchestrator handles the loop:

```python
async def generate_with_tools(context: ConversationContext) -> Response:
    messages = format_messages(context)

    while True:
        # Call LLM
        result = await llm.generate(
            messages=messages,
            tools=context.available_tools,
            personality=context.personality
        )

        if result.is_final:
            return result.content

        # Execute tool calls
        for tool_call in result.tool_calls:
            tool_result = await execute_tool(tool_call)
            messages.append(tool_result_message(tool_call, tool_result))
```

Key design decisions:
- **Max tool iterations**: Cap at 10-20 to prevent infinite loops
- **Parallel tool calls**: When tools are independent, execute concurrently
- **Error handling**: Tool failures return error messages, not exceptions

---

## III. Memory Integration

### Memory Types and Access Patterns

| Memory Type | Store | When to Query | When to Write |
|-------------|-------|---------------|---------------|
| Episodic | SQLite + Qdrant | Semantic similarity to input | After each conversation |
| Semantic | Qdrant (facts) | Always (top-k relevant facts) | When new facts extracted |
| Procedural | SQLite (patterns) | When detecting routine | When pattern repeats |
| Aesthetic | Qdrant (embeddings) | Creative tasks | When preference expressed |

### Integration with Mem0

Using Mem0 as the memory backend (per previous research):

```python
from mem0 import Memory

class MemoryManager:
    def __init__(self, user_id: str):
        self.memory = Memory.from_config({
            "llm": {"provider": "ollama", "model": "qwen2.5:7b"},
            "embedder": {"provider": "ollama", "model": "nomic-embed-text"},
            "vector_store": {"provider": "qdrant", "url": "http://localhost:6333"}
        })
        self.user_id = user_id

    async def get_relevant(self, query: str, limit: int = 10) -> list[Memory]:
        """Retrieve memories relevant to current context."""
        results = self.memory.search(query, user_id=self.user_id, limit=limit)
        return [Memory.from_mem0(r) for r in results]

    async def add_from_conversation(self, messages: list[Message]):
        """Extract and store memories from conversation."""
        # Mem0 handles extraction automatically
        self.memory.add(messages, user_id=self.user_id)
```

### Memory in the Prompt

Inject retrieved memories into the system prompt:

```python
def format_system_prompt(personality: PersonalityConfig, memories: list[Memory]) -> str:
    return f"""
{personality.to_system_prompt()}

## What I Know About You

{format_memories(memories)}

## Current Context

{format_active_context()}
"""
```

---

## IV. Module Routing

### Module Registry

Track available modules and their capabilities:

```python
@dataclass
class Module:
    name: str
    type: ModuleType  # perception, processing, output, tool
    status: ModuleStatus  # healthy, degraded, offline
    capabilities: list[str]
    mcp_server: Optional[str]  # If exposed via MCP

class ModuleRegistry:
    def __init__(self):
        self.modules: dict[str, Module] = {}

    def get_for_capability(self, capability: str) -> Optional[Module]:
        """Find a healthy module that provides a capability."""
        for module in self.modules.values():
            if capability in module.capabilities and module.status == ModuleStatus.HEALTHY:
                return module
        return None

    async def health_check(self):
        """Periodic health check of all modules."""
        for name, module in self.modules.items():
            try:
                # Ping the module
                status = await check_module_health(module)
                module.status = status
            except Exception:
                module.status = ModuleStatus.OFFLINE
```

### Tool Selection

The LLM decides which tools to use, but the orchestrator:
1. Filters available tools based on context
2. Validates tool calls before execution
3. Routes to appropriate MCP server

```python
def get_available_tools(context: ConversationContext) -> list[ToolDefinition]:
    """Return tools appropriate for current context."""
    tools = []

    # Always available
    tools.extend(registry.get_tools_for_type(ToolType.CORE))

    # Context-dependent
    if context.is_creative_task:
        tools.extend(registry.get_tools_for_type(ToolType.CREATIVE))

    if context.has_file_context:
        tools.extend(registry.get_tools_for_type(ToolType.FILESYSTEM))

    # Filter by health
    return [t for t in tools if registry.is_healthy(t.module)]
```

---

## V. State Management

### Session State

What persists during a conversation session:

```python
@dataclass
class SessionState:
    session_id: str
    started_at: datetime

    # Conversation
    messages: list[Message]
    current_intent: Optional[str]  # What user is trying to accomplish

    # Working context
    active_project: Optional[str]
    referenced_files: list[str]
    pending_actions: list[Action]

    # Continuity
    last_tool_results: dict[str, Any]
    unresolved_questions: list[str]
```

### Persistence Strategy

```python
class StateManager:
    def __init__(self, db_path: str):
        self.db = sqlite3.connect(db_path)
        self._init_schema()

    def save_session(self, state: SessionState):
        """Save session for potential resumption."""
        self.db.execute("""
            INSERT OR REPLACE INTO sessions
            (id, started_at, messages, context_json, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            state.session_id,
            state.started_at.isoformat(),
            json.dumps([m.to_dict() for m in state.messages]),
            json.dumps(state.to_context_dict()),
            datetime.now().isoformat()
        ))
        self.db.commit()

    def load_recent_session(self) -> Optional[SessionState]:
        """Load most recent session for continuity."""
        row = self.db.execute("""
            SELECT * FROM sessions
            ORDER BY updated_at DESC LIMIT 1
        """).fetchone()

        if row and self._is_resumable(row):
            return SessionState.from_row(row)
        return None
```

### Intent Tracking

Track what the user is trying to accomplish at multiple levels:

```python
@dataclass
class IntentStack:
    immediate: Optional[str]   # "Find information about X"
    task: Optional[str]        # "Write a research summary"
    project: Optional[str]     # "DAEMON implementation"
    life: Optional[str]        # "Build a local AI companion"

class IntentTracker:
    def update(self, messages: list[Message], response: str) -> IntentStack:
        """Use LLM to extract/update intent from conversation."""
        # Could use a smaller, faster model for this
        result = self.intent_llm.analyze(messages, response)
        return IntentStack(**result)
```

---

## VI. Implementation

### Project Structure

```
daemon/
├── orchestrator/
│   ├── __init__.py
│   ├── core.py           # Main orchestrator class
│   ├── context.py        # Context building
│   ├── memory.py         # Memory integration
│   ├── modules.py        # Module registry
│   ├── state.py          # State management
│   └── prompts.py        # Prompt templates
├── modules/
│   ├── llm/              # LLM interface (Ollama/MLX)
│   ├── speech/           # STT/TTS
│   ├── vision/           # VLM
│   └── tools/            # MCP tool implementations
├── config/
│   ├── personality.yaml  # Personality configuration
│   └── modules.yaml      # Module configuration
└── data/
    ├── daemon.db         # SQLite for state/episodic
    └── qdrant/           # Vector store data
```

### Core Orchestrator Class

```python
class Daemon:
    def __init__(self, config_path: str):
        self.config = load_config(config_path)
        self.personality = PersonalityConfig.load(self.config.personality_path)
        self.memory = MemoryManager(user_id=self.config.user_id)
        self.modules = ModuleRegistry()
        self.state = StateManager(self.config.db_path)
        self.llm = LLMModule(self.config.llm)

    async def start(self):
        """Initialize and start the daemon."""
        await self._load_modules()
        await self._restore_session()
        await self.run()

    async def run(self):
        """Main conversation loop."""
        while True:
            try:
                # Get input (could be text, voice, or event)
                input_event = await self._get_input()

                # Process based on input type
                if input_event.type == InputType.USER_MESSAGE:
                    await self._handle_message(input_event.content)
                elif input_event.type == InputType.SYSTEM_EVENT:
                    await self._handle_event(input_event)

            except KeyboardInterrupt:
                await self._shutdown()
                break

    async def _handle_message(self, content: str):
        """Handle a user message."""
        # Build context
        context = await self._build_context(content)

        # Generate response
        response = await self._generate(context)

        # Update state
        await self._update_state(content, response)

        # Output
        await self._output(response)

    async def _build_context(self, user_input: str) -> ConversationContext:
        """Assemble all context for this turn."""
        return ConversationContext(
            user_input=user_input,
            conversation_history=self.state.current.messages[-10:],
            relevant_memories=await self.memory.get_relevant(user_input),
            active_project=self.state.current.active_project,
            personality=self.personality,
            available_tools=self.modules.get_available_tools(),
            timestamp=datetime.now(),
            session_id=self.state.current.session_id
        )
```

### Startup Sequence

```python
async def main():
    # 1. Load configuration
    daemon = Daemon(config_path="config/daemon.yaml")

    # 2. Start background services
    await daemon.modules.start_health_monitor()

    # 3. Check for resumed session
    if daemon.state.has_recent_session():
        print("Resuming previous session...")
    else:
        print("Starting new session...")

    # 4. Enter conversation loop
    await daemon.run()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## VII. Configuration

### daemon.yaml

```yaml
# Core settings
user_id: "kenny"
db_path: "data/daemon.db"
personality_path: "config/personality.yaml"

# LLM configuration
llm:
  provider: "ollama"
  model: "qwen2.5:72b"
  fallback_model: "qwen2.5:7b"  # If main model unavailable
  temperature: 0.7
  max_tokens: 4096

# Memory configuration
memory:
  provider: "mem0"
  vector_store:
    provider: "qdrant"
    url: "http://localhost:6333"
    collection: "daemon_memories"
  embedder:
    provider: "ollama"
    model: "nomic-embed-text"

# Module configuration
modules:
  speech_to_text:
    enabled: true
    provider: "whisper"
    model: "mlx-community/whisper-large-v3-turbo"

  text_to_speech:
    enabled: true
    provider: "kokoro"
    voice: "af_sarah"

  vision:
    enabled: false  # Enable when needed
    provider: "qwen-vl"
    model: "mlx-community/Qwen2.5-VL-7B-Instruct-4bit"

# MCP servers
mcp_servers:
  - name: "memory"
    command: "npx"
    args: ["-y", "@mem0/mcp-server"]

  - name: "filesystem"
    command: "npx"
    args: ["-y", "@anthropic/mcp-server-filesystem"]
    env:
      ALLOWED_PATHS: "/Users/kenny/Projects,/Users/kenny/Documents"
```

---

## VIII. Error Handling and Resilience

### Graceful Degradation

```python
async def _generate(self, context: ConversationContext) -> str:
    """Generate response with fallback handling."""
    try:
        # Try primary model
        return await self.llm.generate(context)
    except ModelUnavailableError:
        # Fall back to smaller model
        self.llm.use_fallback()
        return await self.llm.generate(context)
    except MemoryRetrievalError:
        # Continue without memory context
        context.relevant_memories = []
        return await self.llm.generate(context)
```

### Module Health Monitoring

```python
class HealthMonitor:
    async def run(self, interval: int = 60):
        """Periodic health check of all modules."""
        while True:
            for module in self.registry.modules.values():
                try:
                    healthy = await module.health_check()
                    module.status = ModuleStatus.HEALTHY if healthy else ModuleStatus.DEGRADED
                except Exception:
                    module.status = ModuleStatus.OFFLINE
                    await self._notify_degradation(module)

            await asyncio.sleep(interval)
```

---

## IX. Next Steps

### Minimum Viable Orchestrator

1. **Text conversation loop** with Ollama
2. **Memory integration** with Mem0
3. **Personality injection** from YAML config
4. **Session persistence** in SQLite

### Then Add

- MCP tool integration
- Voice I/O modules
- Intent tracking
- Health monitoring
- Multi-modal context

---

## References

- [DAEMON Intent Doc](/Users/ellis/Projects/daemon/)
- [MCP Implementation Guide](daemon-mcp-implementation.md)
- [Personality Configuration Guide](daemon-personality-configuration.md)
- [Memory Implementation Guide](local-ai-memory-implementation-guide.md)
- [LLM Selection Guide](daemon-local-llm-selection.md)
