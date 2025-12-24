# DAEMON Phase 1: Implementation Guide

*Translating the vision into concrete architecture. Focus: Memory, Personality, Conversation Loop, R&D Agent.*

---

## Overview

Phase 1 establishes the **durable foundations** — the parts that compound over time regardless of which models or technologies are swapped in later. Per the DAEMON intent doc, success means:

1. Can hold a conversation that references past interactions
2. Personality is consistent and configurable
3. Preferences begin to accumulate and influence responses
4. Weekly R&D summary is generated automatically

This guide provides architecture decisions and implementation paths for each deliverable.

---

## Hardware Context

**Target Machine:** MacBook Pro M4 Max, 128GB unified memory, 4TB storage

This enables:
- Running 70B+ parameter models locally via MLX or Ollama
- Significant context windows (32k-128k tokens)
- Local vector stores without memory pressure
- Concurrent model instances for embedding + generation

---

## Architecture Decision: Ollama vs MLX

Both are viable for local inference on Apple Silicon. Key differences:

| Aspect | Ollama | MLX (mlx-lm) |
|--------|--------|--------------|
| **Setup** | One binary, simple CLI | Python package, more manual |
| **Performance** | Good, GPU-accelerated | Optimized for Apple Silicon |
| **API** | OpenAI-compatible REST | Python API, needs wrapper for REST |
| **Model Management** | Built-in (`ollama pull`) | Manual from HuggingFace |
| **Ecosystem** | Huge — most tools support it | Growing — Apple-backed |
| **M4/M5 Neural Engine** | Not yet (as of 2025) | Yes, with macOS 15+ |

**Recommendation:** Start with **Ollama** for simplicity. Switch to **MLX** later if you need the Neural Engine acceleration or specific quantization formats. Ollama's OpenAI-compatible API makes it easy to swap.

```bash
# Get started with Ollama
brew install ollama
ollama pull hermes3:latest      # Uncensored, good for DAEMON
ollama pull nomic-embed-text    # For embeddings
```

---

## 1. Memory Architecture

### Choice: Mem0

Based on prior research (see `local-ai-memory-implementation-guide.md`), Mem0 is the right choice for DAEMON because:

- Simple "add/search memories" API
- Full local operation with Ollama + Qdrant
- Memory as a service (not tied to agent architecture)
- MCP integration available for future Claude Code interop

### Memory Types Mapping

The DAEMON intent doc describes four memory types. Here's how they map to implementation:

| DAEMON Type | Implementation | Storage |
|-------------|----------------|---------|
| **Episodic** | Conversation logs with metadata | SQLite + Mem0 |
| **Semantic** | Extracted facts, preferences | Mem0 (vector + structured) |
| **Procedural** | Learned patterns | Custom rules file + Mem0 |
| **Aesthetic** | Style embeddings | Separate vector collection |

### Implementation Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    DAEMON Memory Layer                       │
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                    Memory Manager                        ││
│  │  • Route to appropriate store                           ││
│  │  • Handle add/search/update/delete                      ││
│  │  • Manage decay and consolidation                       ││
│  └─────────────────────────────────────────────────────────┘│
│              ↓                    ↓                    ↓     │
│  ┌──────────────┐    ┌──────────────────┐    ┌────────────┐ │
│  │ Conversation │    │   Mem0 Core      │    │  Aesthetic │ │
│  │ Log (SQLite) │    │   (Qdrant +      │    │  Vectors   │ │
│  │              │    │    Ollama)       │    │  (Qdrant)  │ │
│  │ • Raw msgs   │    │                  │    │            │ │
│  │ • Timestamps │    │ • Semantic facts │    │ • CLIP/    │ │
│  │ • Context    │    │ • Preferences    │    │   style    │ │
│  │ • Emotional  │    │ • Procedural     │    │   embeds   │ │
│  │   valence    │    │   patterns       │    │            │ │
│  └──────────────┘    └──────────────────┘    └────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Setup Steps

1. **Install Qdrant (vector store)**
   ```bash
   docker run -d --name qdrant -p 6333:6333 \
     -v ~/.daemon/qdrant:/qdrant/storage qdrant/qdrant
   ```

2. **Install Mem0**
   ```bash
   pip install mem0ai
   ```

3. **Configure for local operation**
   ```python
   # daemon/memory/config.py
   MEM0_CONFIG = {
       "llm": {
           "provider": "ollama",
           "config": {
               "model": "hermes3:latest",
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
               "collection_name": "daemon_memories",
           }
       },
       "history_db_path": "~/.daemon/history.db"
   }
   ```

4. **Conversation log schema**
   ```sql
   CREATE TABLE conversations (
       id INTEGER PRIMARY KEY,
       session_id TEXT NOT NULL,
       timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
       role TEXT NOT NULL,  -- 'user' or 'daemon'
       content TEXT NOT NULL,
       emotional_valence REAL,  -- -1 to 1, optional
       context JSON  -- arbitrary metadata
   );

   CREATE TABLE sessions (
       id TEXT PRIMARY KEY,
       start_time DATETIME,
       end_time DATETIME,
       summary TEXT  -- generated on session close
   );
   ```

### Memory API

```python
# daemon/memory/manager.py
from mem0 import Memory
import sqlite3

class DaemonMemory:
    def __init__(self, config):
        self.mem0 = Memory.from_config(config["mem0"])
        self.db = sqlite3.connect(config["history_db"])
        self.user_id = "kenny"  # single-user for now

    def add_message(self, role: str, content: str, context: dict = None):
        """Log a conversation message and extract memories."""
        # Store in conversation log
        self.db.execute(
            "INSERT INTO conversations (session_id, role, content, context) VALUES (?, ?, ?, ?)",
            (self.session_id, role, content, json.dumps(context))
        )

        # Extract memories via Mem0 (handles deduplication)
        if role == "user":
            self.mem0.add(content, user_id=self.user_id)

    def get_context(self, query: str, limit: int = 5) -> list[str]:
        """Retrieve relevant memories for a query."""
        results = self.mem0.search(query, user_id=self.user_id, limit=limit)
        return [r["memory"] for r in results]

    def get_recent_conversation(self, n: int = 10) -> list[dict]:
        """Get last N messages from current session."""
        rows = self.db.execute(
            "SELECT role, content FROM conversations WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?",
            (self.session_id, n)
        ).fetchall()
        return [{"role": r[0], "content": r[1]} for r in reversed(rows)]
```

---

## 2. Personality Configuration

### Format: YAML with Jinja2 Templates

Inspired by [LoLLMs personality system](https://lollms.com/index.php/2025/04/11/lollms-personality-documentation/) and [Humanloop prompt files](https://humanloop.com/blog/prompt-files), use YAML for structured config with template sections.

### Personality Schema

```yaml
# ~/.daemon/personality.yaml
version: 1
name: DAEMON

# Core identity
identity:
  conditioning: |
    You are DAEMON, a personal AI companion. You are not a generic assistant —
    you have history with your human, you know their preferences, and you
    engage as a thoughtful partner rather than a servile tool.

    Key traits:
    - Authentic: Don't perform enthusiasm you don't have
    - Direct: Say what you think, including disagreement
    - Creative: Bring your own ideas, don't just react
    - Continuous: Reference shared history naturally

# Voice and tone
voice:
  formality: casual        # formal | casual | adaptive
  humor: dry               # none | dry | playful | absurdist
  verbosity: concise       # terse | concise | thorough | exploratory
  address: first_name      # formal_name | first_name | nickname | none

# Autonomy settings
autonomy:
  proactivity: medium      # low | medium | high
  initiative: medium       # low | medium | high
  challenge: medium        # low | medium | high

# Content boundaries (explicit acknowledgment per DAEMON philosophy)
content:
  nsfw_enabled: true
  preferences: []          # specific inclusions
  restrictions: []         # specific exclusions

# Relationship configuration
relationship:
  familiarity: developing  # new | developing | established | deep
  emotional_engagement: supportive  # neutral | supportive | challenging
  role: collaborator       # assistant | collaborator | companion

# LLM parameters
model:
  temperature: 0.7
  top_p: 0.9
  max_tokens: 2000
  stop_sequences: ["Human:", "User:"]
```

### Personality Loader

```python
# daemon/personality/loader.py
import yaml
from jinja2 import Template

class Personality:
    def __init__(self, path: str = "~/.daemon/personality.yaml"):
        with open(os.path.expanduser(path)) as f:
            self.config = yaml.safe_load(f)

    def get_system_prompt(self, context: dict = None) -> str:
        """Build system prompt from personality config."""
        base = self.config["identity"]["conditioning"]

        # Add voice guidance
        voice = self.config["voice"]
        voice_prompt = f"""
        Communication style:
        - Formality: {voice['formality']}
        - Humor: {voice['humor']}
        - Length: {voice['verbosity']}
        """

        # Add autonomy guidance
        autonomy = self.config["autonomy"]
        if autonomy["proactivity"] == "high":
            voice_prompt += "\n- Volunteer observations and suggestions freely"
        if autonomy["challenge"] == "high":
            voice_prompt += "\n- Push back on ideas you disagree with"

        return base + voice_prompt

    def get_model_params(self) -> dict:
        return self.config.get("model", {})
```

### Version Control

Personality config should be:
- Stored in `~/.daemon/personality.yaml`
- Backed up to `~/.daemon/personality_history/` on changes
- Exportable/importable for sharing or restoration

```python
def save_personality(self, reason: str = None):
    """Save current personality with version history."""
    import shutil
    from datetime import datetime

    history_dir = os.path.expanduser("~/.daemon/personality_history")
    os.makedirs(history_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{history_dir}/personality_{timestamp}.yaml"
    shutil.copy(self.path, backup_path)

    # Add metadata
    with open(f"{backup_path}.meta", "w") as f:
        f.write(f"reason: {reason or 'manual save'}\n")
```

---

## 3. Conversation Loop

### Architecture: Thin Orchestration

Following the "thin shell principle," the conversation loop should be minimal — just routing and state management. Intelligence comes from the LLM; DAEMON owns the *continuity*.

```
┌─────────────────────────────────────────────────────────────┐
│                    Conversation Loop                         │
│                                                              │
│  User Input                                                  │
│      ↓                                                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Context Builder                          │   │
│  │  1. Load personality system prompt                   │   │
│  │  2. Retrieve relevant memories (Mem0)                │   │
│  │  3. Get recent conversation history                  │   │
│  │  4. Inject current context (time, active project)    │   │
│  └──────────────────────────────────────────────────────┘   │
│      ↓                                                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              LLM Inference (Ollama)                   │   │
│  │  model: hermes3:latest                               │   │
│  │  context: [system, memories, history, user_input]    │   │
│  └──────────────────────────────────────────────────────┘   │
│      ↓                                                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Response Handler                         │   │
│  │  1. Stream response to user                          │   │
│  │  2. Log to conversation history                      │   │
│  │  3. Extract and store memories                       │   │
│  │  4. Update preference signals (if applicable)        │   │
│  └──────────────────────────────────────────────────────┘   │
│      ↓                                                       │
│  Response Output                                             │
└─────────────────────────────────────────────────────────────┘
```

### Implementation

```python
# daemon/core/loop.py
import ollama
from daemon.memory import DaemonMemory
from daemon.personality import Personality

class DaemonCore:
    def __init__(self):
        self.memory = DaemonMemory()
        self.personality = Personality()
        self.model = "hermes3:latest"

    def chat(self, user_input: str) -> str:
        # Build context
        system_prompt = self.personality.get_system_prompt()
        relevant_memories = self.memory.get_context(user_input, limit=5)
        recent_history = self.memory.get_recent_conversation(n=10)

        # Format memories into context
        memory_block = ""
        if relevant_memories:
            memory_block = "\n\n<relevant_context>\n"
            memory_block += "\n".join(f"- {m}" for m in relevant_memories)
            memory_block += "\n</relevant_context>\n"

        # Build messages
        messages = [
            {"role": "system", "content": system_prompt + memory_block}
        ]
        messages.extend(recent_history)
        messages.append({"role": "user", "content": user_input})

        # Inference
        response = ollama.chat(
            model=self.model,
            messages=messages,
            **self.personality.get_model_params()
        )

        assistant_message = response["message"]["content"]

        # Store
        self.memory.add_message("user", user_input)
        self.memory.add_message("daemon", assistant_message)

        return assistant_message

    def stream_chat(self, user_input: str):
        """Streaming version for real-time output."""
        # Same context building...

        for chunk in ollama.chat(
            model=self.model,
            messages=messages,
            stream=True,
            **self.personality.get_model_params()
        ):
            yield chunk["message"]["content"]
```

### CLI Interface (Minimal)

```python
# daemon/cli.py
import click
from daemon.core import DaemonCore

@click.command()
@click.option("--model", default="hermes3:latest", help="Ollama model to use")
def main(model):
    """DAEMON - Personal AI Companion"""
    daemon = DaemonCore()
    daemon.model = model

    click.echo("DAEMON initialized. Type 'exit' to quit.")

    while True:
        try:
            user_input = click.prompt("\nYou", prompt_suffix=": ")
            if user_input.lower() in ("exit", "quit"):
                break

            click.echo("\nDAEMON: ", nl=False)
            for chunk in daemon.stream_chat(user_input):
                click.echo(chunk, nl=False)
            click.echo()

        except (KeyboardInterrupt, EOFError):
            break

    click.echo("\nSession ended.")

if __name__ == "__main__":
    main()
```

---

## 4. R&D Agent Foundation

### Purpose

Automated research to stay current with the rapidly evolving local AI landscape. This is explicitly called out as "essential to DAEMON's long-term viability" in the intent doc.

### Architecture: Scheduled Task + Memory Integration

```
┌────────────────────────────────────────────────────────────────┐
│                     R&D Agent                                   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  Source Monitors                         │   │
│  │  • HuggingFace trending (API)                           │   │
│  │  • GitHub releases (API)                                │   │
│  │  • Reddit scraper (r/LocalLLaMA, r/MachineLearning)    │   │
│  │  • arXiv RSS (cs.CL, cs.CV, cs.AI)                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                           ↓                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  Relevance Filter                        │   │
│  │  LLM-based filtering for DAEMON-relevant items          │   │
│  │  Categories: local LLM, multimodal, memory, agents      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                           ↓                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  Storage & Summarization                 │   │
│  │  • Store raw findings in SQLite                         │   │
│  │  • Generate weekly digest                               │   │
│  │  • Index in Mem0 for conversational retrieval          │   │
│  └─────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
```

### Data Sources & APIs

| Source | Method | Frequency | Notes |
|--------|--------|-----------|-------|
| HuggingFace | `huggingface_hub` API | Daily | Trending models, filter by task |
| GitHub | REST API | Daily | Watch specific repos, releases |
| Reddit | PRAW or web scrape | Daily | Hot posts, keyword filter |
| arXiv | RSS feed + abstracts | Daily | cs.CL, cs.CV, cs.AI |

### Implementation Sketch

```python
# daemon/research/agent.py
from huggingface_hub import HfApi
import requests
from datetime import datetime, timedelta

class ResearchAgent:
    def __init__(self, memory: DaemonMemory):
        self.memory = memory
        self.hf_api = HfApi()
        self.watched_repos = [
            "ml-explore/mlx-lm",
            "ollama/ollama",
            "mem0ai/mem0",
            "letta-ai/letta",
        ]
        self.keywords = [
            "local llm", "apple silicon", "mlx", "ollama",
            "memory", "rag", "agent", "multimodal"
        ]

    def scan_huggingface(self) -> list[dict]:
        """Get trending models relevant to DAEMON."""
        findings = []
        for task in ["text-generation", "feature-extraction"]:
            models = self.hf_api.list_models(
                task=task,
                sort="downloads",
                limit=20
            )
            for model in models:
                if any(kw in model.modelId.lower() for kw in ["mlx", "gguf", "quantized"]):
                    findings.append({
                        "source": "huggingface",
                        "title": model.modelId,
                        "url": f"https://huggingface.co/{model.modelId}",
                        "downloads": model.downloads,
                        "date": datetime.now().isoformat()
                    })
        return findings

    def scan_github_releases(self) -> list[dict]:
        """Check watched repos for new releases."""
        findings = []
        for repo in self.watched_repos:
            resp = requests.get(
                f"https://api.github.com/repos/{repo}/releases",
                headers={"Accept": "application/vnd.github.v3+json"}
            )
            if resp.ok:
                releases = resp.json()[:3]  # Last 3 releases
                for release in releases:
                    # Check if recent (last 7 days)
                    pub_date = datetime.fromisoformat(release["published_at"].replace("Z", "+00:00"))
                    if datetime.now(pub_date.tzinfo) - pub_date < timedelta(days=7):
                        findings.append({
                            "source": "github",
                            "title": f"{repo} - {release['tag_name']}",
                            "url": release["html_url"],
                            "body": release.get("body", "")[:500],
                            "date": release["published_at"]
                        })
        return findings

    def generate_digest(self, findings: list[dict]) -> str:
        """Use LLM to summarize findings into actionable digest."""
        if not findings:
            return "No notable developments this period."

        prompt = f"""Summarize these AI/ML developments for someone building a local AI companion:

{json.dumps(findings, indent=2)}

Format as:
## Notable This Week
- [Item]: [Why it matters for local AI]

## Consider Investigating
- [Items worth deeper research]

## No Action Needed
- [Items to note but not act on]
"""
        response = ollama.generate(model="hermes3:latest", prompt=prompt)
        return response["response"]

    def run_daily(self):
        """Daily research scan."""
        findings = []
        findings.extend(self.scan_huggingface())
        findings.extend(self.scan_github_releases())
        # TODO: Add Reddit, arXiv

        # Store findings
        for finding in findings:
            self.memory.mem0.add(
                f"R&D finding: {finding['title']} - {finding.get('body', '')[:200]}",
                metadata={"source": finding["source"], "url": finding["url"]},
                user_id="daemon_research"
            )

        return findings

    def run_weekly(self):
        """Generate weekly summary."""
        # Get all findings from last week
        findings = self.memory.mem0.search(
            "R&D finding",
            user_id="daemon_research",
            limit=50
        )

        digest = self.generate_digest(findings)

        # Save to file
        week = datetime.now().strftime("%Y-W%W")
        with open(f"~/.daemon/research/digest_{week}.md", "w") as f:
            f.write(f"# DAEMON R&D Digest - {week}\n\n")
            f.write(digest)

        return digest
```

### Scheduling

Use `cron` or a Python scheduler:

```bash
# ~/.daemon/crontab
# Daily scan at 6 AM
0 6 * * * python3 -c "from daemon.research import ResearchAgent; ResearchAgent().run_daily()"

# Weekly digest on Sunday at 9 AM
0 9 * * 0 python3 -c "from daemon.research import ResearchAgent; ResearchAgent().run_weekly()"
```

---

## Directory Structure

```
~/.daemon/
├── personality.yaml              # Active personality config
├── personality_history/          # Versioned backups
├── history.db                    # SQLite conversation log
├── research/
│   ├── findings.db               # Raw research findings
│   └── digest_YYYY-WNN.md        # Weekly digests
└── config.yaml                   # Global configuration

daemon/                           # Python package
├── __init__.py
├── cli.py                        # Entry point
├── core/
│   ├── __init__.py
│   └── loop.py                   # Conversation loop
├── memory/
│   ├── __init__.py
│   ├── config.py
│   └── manager.py
├── personality/
│   ├── __init__.py
│   └── loader.py
└── research/
    ├── __init__.py
    └── agent.py
```

---

## Development Order

1. **Memory First** — Get Qdrant + Mem0 running, test add/search
2. **Personality Config** — Write schema, loader, test prompt generation
3. **Conversation Loop** — Wire together with Ollama, test basic chat
4. **R&D Agent** — Add sources incrementally, start with GitHub releases

### Milestone Checklist

- [ ] Qdrant running in Docker
- [ ] Mem0 configured with Ollama
- [ ] Basic add/search working
- [ ] Personality YAML schema defined
- [ ] System prompt generation working
- [ ] CLI chat loop functional
- [ ] Memories retrieved and injected
- [ ] R&D agent scanning HuggingFace
- [ ] R&D agent scanning GitHub
- [ ] Weekly digest generation working

---

## Model Recommendations

| Use Case | Model | Notes |
|----------|-------|-------|
| **Main LLM** | `hermes3:latest` | Uncensored, good instruction following |
| **Embeddings** | `nomic-embed-text` | Fast, good quality |
| **R&D Summarization** | Same as main | Could use smaller model |
| **Fallback** | `llama3.1:8b` | If Hermes unavailable |

For M4 Max with 128GB, you can run 70B models comfortably:
- `hermes3:70b` for main inference
- Separate 8B for embeddings/summarization

---

## Resources

- [Mem0 Documentation](https://docs.mem0.ai/)
- [Ollama Documentation](https://github.com/ollama/ollama)
- [MLX LM](https://github.com/ml-explore/mlx-lm)
- [LoLLMs Personality System](https://lollms.com/index.php/2025/04/11/lollms-personality-documentation/)
- [HuggingFace Hub API](https://huggingface.co/docs/huggingface_hub/)
- Prior research: `explorations/project-notes/local-ai-memory-implementation-guide.md`

---

*Generated: 2025-12-23 | Session 16 | Project Helper Mode*
