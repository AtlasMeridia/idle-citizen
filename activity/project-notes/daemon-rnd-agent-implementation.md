# DAEMON R&D Agent: Implementation Guide

*A practical guide to building the automated research monitoring system described in the DAEMON intent document.*

---

## Overview

DAEMON's R&D Agent is described as "essential to DAEMON's long-term viability" — a system that monitors the rapidly evolving AI landscape and surfaces relevant developments. This guide provides concrete implementation paths for each data source.

**Goal:** Automate the tedious work of keeping up with AI developments so Kenny can make informed decisions about which technologies to integrate.

---

## Architecture Recommendation

### Approach: Python-based Aggregator with SQLite + Datasette

**Why this stack:**
- Python has mature libraries for all data sources (PRAW, feedparser, PyGithub)
- SQLite stores all collected data in a single, queryable file
- Datasette provides instant web UI for browsing/filtering without additional code
- Runs locally, no external dependencies except APIs
- Extensible — add new sources by adding collectors

**High-level flow:**
```
[Collectors] → [SQLite DB] → [Datasette UI] → [Weekly digest generator]
     ↓
   Cron/launchd scheduled
```

---

## Data Source Implementation

### 1. HuggingFace Trending Models

**API Access:**
- HuggingFace Hub API: `huggingface_hub` Python library
- Trending page scraping: `huggingface/trending-deploy` GitHub repo

**Implementation:**
```python
from huggingface_hub import HfApi

api = HfApi()

# Get trending models by task
models = api.list_models(
    sort="downloads",
    direction=-1,
    limit=50,
    filter="text-generation"  # or "automatic-speech-recognition", etc.
)

# Key fields: model_id, downloads, likes, last_modified, tags
```

**Relevant filters for DAEMON:**
- `text-generation` — LLM core candidates
- `automatic-speech-recognition` — STT module
- `text-to-speech` — TTS module
- `image-to-text`, `visual-question-answering` — Vision modules
- `text-to-image` — Image generation

**Frequency:** Daily

**Links:**
- [HuggingFace Models API](https://huggingface.co/models)
- [huggingface/trending-deploy](https://github.com/huggingface/trending-deploy)

---

### 2. arXiv Papers

**API Access:**
- Official RSS: `http://export.arxiv.org/rss/cs.CL` (and other categories)
- Atom API: More flexible querying with `http://export.arxiv.org/api/query`

**Implementation:**
```python
import feedparser

# RSS feed for Computation and Language
feed = feedparser.parse("http://export.arxiv.org/rss/cs.CL")

# Or use Atom API for more control
import urllib.request

query = "cat:cs.CL+OR+cat:cs.LG+OR+cat:cs.AI+OR+cat:cs.CV"
url = f"http://export.arxiv.org/api/query?search_query={query}&start=0&max_results=100&sortBy=submittedDate&sortOrder=descending"

with urllib.request.urlopen(url) as response:
    content = response.read()
# Parse with feedparser or xml.etree
```

**Relevant categories for DAEMON:**
- `cs.CL` — Computation and Language (NLP, LLMs)
- `cs.LG` — Machine Learning (training techniques, architectures)
- `cs.AI` — Artificial Intelligence (agents, reasoning)
- `cs.CV` — Computer Vision (multimodal, image understanding)
- `cs.SD` — Sound (speech synthesis, audio generation)

**Filtering strategy:**
- Keyword matching on titles/abstracts: "local", "efficient", "quantization", "Apple Silicon", "MLX", "memory", "retrieval", "agent", "personalization"
- Score by keyword density for relevance ranking

**Frequency:** Daily

**Links:**
- [arXiv RSS Feeds](https://info.arxiv.org/help/rss.html)
- [arXiv API docs](https://arxiv.org/help/api/)

---

### 3. Reddit r/LocalLLaMA

**API Access:**
- PRAW (Python Reddit API Wrapper) — requires Reddit app credentials

**Setup:**
```bash
pip install praw
```

**Implementation:**
```python
import praw

reddit = praw.Reddit(
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
    user_agent="daemon-rnd-agent/1.0"
)

subreddit = reddit.subreddit("LocalLLaMA")

# Get hot posts above score threshold
for post in subreddit.hot(limit=50):
    if post.score >= 100:  # High-upvote threshold
        print(f"{post.title} — Score: {post.score}")
        # Store: title, score, url, created_utc, num_comments
```

**Subreddits for DAEMON:**
- `r/LocalLLaMA` — Primary source for local model news
- `r/MachineLearning` — Academic/research perspective
- `r/StableDiffusion` — Image generation (secondary)
- `r/Oobabooga` — Text generation UI ecosystem (optional)

**Filtering:**
- Score threshold (100+ for r/LocalLLaMA)
- Flair: "News", "Tutorial", "Resource"
- Keywords: model names, "benchmark", "release", "quantization", "MLX"

**Frequency:** Daily

**Links:**
- [PRAW Documentation](https://praw.readthedocs.io/)
- [Reddit API Guide](https://www.jcchouinard.com/reddit-api/)

---

### 4. GitHub Releases & Trending

**API Access:**
- PyGithub or GitHub REST API directly
- For trending: third-party APIs since GitHub doesn't have official trending endpoint

**Implementation — Release Monitoring:**
```python
from github import Github

g = Github("YOUR_TOKEN")

# Repos to watch for DAEMON
watchlist = [
    "ggerganov/llama.cpp",
    "ollama/ollama",
    "ml-explore/mlx-examples",
    "huggingface/transformers",
    "OpenBMB/ChatDev",
    "langchain-ai/langchain",
    "mem0ai/mem0",
]

for repo_name in watchlist:
    repo = g.get_repo(repo_name)
    releases = repo.get_releases()
    latest = releases[0] if releases.totalCount > 0 else None
    if latest:
        print(f"{repo_name}: {latest.tag_name} ({latest.published_at})")
```

**Implementation — Trending:**
```python
# Use third-party API (huchenme/github-trending-api or NiklasTiede/Github-Trending-API)
import requests

# Daily trending Python repos
resp = requests.get("https://api.gitterapp.com/repositories?language=python&since=daily")
trending = resp.json()
```

**Repos to watch:**
- LLM inference: `llama.cpp`, `ollama`, `vllm`, `exllamav2`
- Apple Silicon: `mlx`, `mlx-examples`, `mlx-lm`
- Memory systems: `mem0ai/mem0`, `letta-ai/letta`
- Agents: `langchain`, `autogen`, `crewai`
- Speech: `openai/whisper`, `myshell-ai/OpenVoice`

**Frequency:**
- Releases: Daily
- Trending: Weekly

**Links:**
- [Github-Trending-API](https://github.com/NiklasTiede/Github-Trending-API)
- [PyGithub](https://github.com/PyGithub/PyGithub)

---

## Database Schema

```sql
CREATE TABLE arxiv_papers (
    id TEXT PRIMARY KEY,
    title TEXT,
    summary TEXT,
    categories TEXT,
    published TEXT,
    authors TEXT,
    pdf_url TEXT,
    relevance_score REAL,
    collected_at TEXT
);

CREATE TABLE hf_models (
    model_id TEXT PRIMARY KEY,
    task TEXT,
    downloads INTEGER,
    likes INTEGER,
    last_modified TEXT,
    tags TEXT,
    collected_at TEXT
);

CREATE TABLE reddit_posts (
    id TEXT PRIMARY KEY,
    subreddit TEXT,
    title TEXT,
    score INTEGER,
    num_comments INTEGER,
    url TEXT,
    created_utc INTEGER,
    flair TEXT,
    collected_at TEXT
);

CREATE TABLE github_releases (
    id TEXT PRIMARY KEY,
    repo TEXT,
    tag_name TEXT,
    name TEXT,
    body TEXT,
    published_at TEXT,
    collected_at TEXT
);

CREATE TABLE github_trending (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repo TEXT,
    description TEXT,
    language TEXT,
    stars INTEGER,
    forks INTEGER,
    stars_today INTEGER,
    collected_date TEXT
);
```

---

## Digest Generation

**Weekly digest format:**

```markdown
# DAEMON R&D Digest — Week of YYYY-MM-DD

## 🔥 High-Priority Updates
- [llama.cpp v0.X.X released with MLX support](link)
- [New 70B model quantized to 4-bit runs on M3 Max](reddit link)

## 📄 Notable Papers
1. **Title** (cs.CL) — Brief summary. [PDF](link)
2. **Title** (cs.LG) — Brief summary. [PDF](link)

## 🆕 New Models
- model-name: Task, X downloads, [HF](link)

## 📊 Trending Repos
- repo-name: Description, +X stars this week

## 💡 Considerations for DAEMON
- Potential LLM upgrade: [model] shows improved...
- New memory approach: [paper] suggests...
```

**Implementation:** Python script that queries SQLite, ranks by relevance, and outputs markdown.

---

## Implementation Phases

### Phase 1: Minimal Viable Collector (1-2 hours)
- Single Python script with arXiv + HuggingFace collectors
- SQLite storage
- Manual run via command line
- Output: JSON or markdown summary

### Phase 2: Add Reddit + GitHub (2-3 hours)
- Set up Reddit app credentials
- Add GitHub token for API access
- Expand database schema
- Add to collector script

### Phase 3: Automation + Datasette (1-2 hours)
- Add launchd plist for daily runs
- Install Datasette for browsing
- Create canned queries for common views

### Phase 4: Digest Generation (2-3 hours)
- Weekly digest script
- Relevance scoring algorithm
- Markdown output (could feed into DAEMON's memory)

---

## Starter Code

Full working collector available at: *(to be implemented)*

```python
#!/usr/bin/env python3
"""
DAEMON R&D Agent — Minimal Collector
Collects from arXiv and HuggingFace, stores in SQLite.
"""

import sqlite3
import feedparser
from huggingface_hub import HfApi
from datetime import datetime

DB_PATH = "rnd_agent.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS arxiv_papers (
            id TEXT PRIMARY KEY,
            title TEXT,
            summary TEXT,
            categories TEXT,
            published TEXT,
            collected_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS hf_models (
            model_id TEXT PRIMARY KEY,
            task TEXT,
            downloads INTEGER,
            likes INTEGER,
            collected_at TEXT
        )
    """)
    conn.commit()
    return conn

def collect_arxiv(conn):
    categories = ["cs.CL", "cs.LG", "cs.AI"]
    for cat in categories:
        feed = feedparser.parse(f"http://export.arxiv.org/rss/{cat}")
        for entry in feed.entries:
            conn.execute("""
                INSERT OR REPLACE INTO arxiv_papers
                (id, title, summary, categories, published, collected_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                entry.id, entry.title, entry.summary,
                cat, entry.published, datetime.now().isoformat()
            ))
    conn.commit()

def collect_hf_models(conn):
    api = HfApi()
    tasks = ["text-generation", "automatic-speech-recognition"]
    for task in tasks:
        models = api.list_models(sort="downloads", direction=-1, limit=20, filter=task)
        for m in models:
            conn.execute("""
                INSERT OR REPLACE INTO hf_models
                (model_id, task, downloads, likes, collected_at)
                VALUES (?, ?, ?, ?, ?)
            """, (m.modelId, task, m.downloads, m.likes, datetime.now().isoformat()))
    conn.commit()

if __name__ == "__main__":
    conn = init_db()
    collect_arxiv(conn)
    collect_hf_models(conn)
    print(f"Collection complete. Data stored in {DB_PATH}")
```

---

## Recommendations

1. **Start with Phase 1** — Get something running before optimizing
2. **Store raw data** — Filter and score at query time, not collection time
3. **Use Datasette early** — Free web UI for browsing without code
4. **Connect to DAEMON memory** — Digest outputs could feed into DAEMON's semantic memory
5. **Consider Idle Citizen integration** — This R&D agent could run as an Idle Citizen activity

---

## References

- [HuggingFace Hub API](https://huggingface.co/docs/huggingface_hub/)
- [arXiv RSS Feeds](https://info.arxiv.org/help/rss.html)
- [PRAW Documentation](https://praw.readthedocs.io/)
- [PyGithub](https://github.com/PyGithub/PyGithub)
- [Github-Trending-API](https://github.com/NiklasTiede/Github-Trending-API)
- [Datasette](https://datasette.io/)
- [DAEMON Intent Document](/Users/ellis/Projects/daemon/DAEMON%20Project%20-%20Documentation%20of%20Intent.md)
