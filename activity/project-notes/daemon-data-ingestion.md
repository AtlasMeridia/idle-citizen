# DAEMON Data Ingestion and Memory Bootstrapping Guide

**Created:** 2025-12-24 (Session 35)
**Purpose:** Implementation guide for seeding DAEMON's memory with existing user data
**Status:** Research Document

---

## Overview

DAEMON's value compounds over time as it builds understanding of its user. However, starting from zero means months of conversations before useful context accumulates. This guide covers how to **bootstrap** DAEMON's memory system using existing data sources—giving it a head start on understanding the user from day one.

The goal: by the end of initial ingestion, DAEMON should know:
- User's communication preferences and style
- Active projects and their context
- Technical preferences (tools, languages, approaches)
- Aesthetic preferences (visual style, design sensibilities)
- Recurring themes and interests

---

## 1. Data Sources to Ingest

### Claude Conversation Exports

**Access Methods:**
- Official export: Settings > Privacy in Claude Desktop → ZIP with JSON
- Claude Code: JSONL files in `~/.claude/projects/`
- Third-party: [claude-conversation-extractor](https://github.com/ZeroSumQuant/claude-conversation-extractor) for Claude Code history

**Value for DAEMON:**
- Rich dialogue examples (how user phrases requests, what explanations they appreciate)
- Domain expertise (topics of conversation)
- Problem-solving patterns
- Correction patterns (when user says "no, I meant...")

**Extraction Pattern:**
```python
import json
from pathlib import Path

def extract_conversations(export_path: Path):
    """Parse Claude conversation export"""
    with open(export_path) as f:
        data = json.load(f)

    for conv in data['conversations']:
        yield {
            'id': conv['uuid'],
            'created': conv['created_at'],
            'messages': [
                {'role': m['sender'], 'content': m['text']}
                for m in conv['chat_messages']
            ],
            'summary': conv.get('summary', conv['name'])
        }
```

### Obsidian Vault Notes

**Access Methods:**
- Direct filesystem access to vault folder
- Use [obsidianmd-parser](https://codeberg.org/paddyd/obsidianmd-parser) for Python 3.12+

**Value for DAEMON:**
- Personal knowledge structure (how user organizes thought)
- Recurring themes (tag patterns)
- Unfinished projects (task lists = active goals)
- Relationship networks (wikilink graphs reveal mental models)

**Extraction Pattern:**
```python
from obsidianmd_parser import ObsidianParser

def extract_obsidian(vault_path: str):
    """Parse Obsidian vault for notes and metadata"""
    parser = ObsidianParser(vault_path)

    for note in parser.parse_all():
        yield {
            'title': note.title,
            'path': note.path,
            'frontmatter': note.frontmatter,  # YAML dict
            'content': note.content,
            'wikilinks': note.wikilinks,
            'tags': note.tags,
            'modified': note.modified_time
        }
```

### Creative Work Corpus

**What to Include:**
- Writing samples (essays, drafts, notes)
- Code repositories (source files showing style preferences)
- Images (designs, screenshots, saved references)
- Design files (color palettes, typography choices)

**Value for DAEMON:**
- Communication style (mimicking user's voice)
- Technical preferences (languages, frameworks, patterns)
- Visual aesthetic (composition, color, mood)

### Browser History & Bookmarks

**Access Methods:**
- Chrome: Export via Settings > Downloads (HTML file)
- Firefox: Profile folder `~/.mozilla/firefox/`
- Cross-browser: [HackBrowserData](https://github.com/moonD4rk/HackBrowserData) (security research tool)

**Value for DAEMON:**
- Research interests and patterns
- Domain expertise (documentation sites visited)
- Information consumption habits
- Learning patterns (tutorials revisited)

### Calendar & Email (Privacy-Aware)

**Recommended Approach:**
- Only ingest event titles and timing (not full content)
- Extract patterns: work hours, meeting frequency
- Optional: Email subject lines only
- Apply privacy filters aggressively (see Section 5)

**Value for DAEMON:**
- Schedule preferences
- Project timelines
- Recurring commitments
- Role/title context

---

## 2. Ingestion Pipeline Architecture

### High-Level Flow

```
Raw Data Sources → Extraction → Parsing → Filtering → Embedding → Storage
                                              ↓
                                         Privacy Gate
                                              ↓
                                      Deduplication
```

### Pipeline Components

**1. Extraction Phase**
- Use language-specific parsers (Python libraries for most formats)
- Handle encoding issues (UTF-8, special characters)
- Preserve source metadata (filename, timestamp, source type)
- Stream large datasets (don't load everything into memory)

**2. Parsing Phase**
```python
# Normalize to common schema
parsed_item = {
    'source': 'obsidian|claude|browser',
    'source_path': '/path/to/file',
    'content': 'The actual text content',
    'metadata': {
        'timestamp': '2025-12-24T10:30:00Z',
        'tags': ['project', 'research'],
        'entities': ['DAEMON', 'Mem0', 'Qdrant']
    }
}
```

**3. Filtering Phase (Privacy Gate)**
- Pattern matching for PII (SSN, credit cards, phone numbers)
- Semantic classification for sensitive content
- User-controlled allowlisting

**4. Embedding Phase**
```python
import ollama

def embed_batch(documents: list[str], batch_size: int = 100):
    """Efficient batched embedding with Ollama"""
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i+batch_size]
        response = ollama.embed(
            model='nomic-embed-text',
            input=batch
        )
        yield from response['embeddings']
```

**5. Storage Phase**
- Use Mem0 for structured memory (facts, preferences)
- Use Qdrant for raw vector search
- Maintain source citations for traceability

---

## 3. Memory Bootstrapping: From Raw Data to Structured Knowledge

### Three-Layer Memory Model

```
Layer 0: Raw Storage
├─ Conversation logs (SQLite)
├─ Document text (file storage)
└─ Metadata indices

Layer 1: Extracted Facts (Mem0)
├─ Entity extraction: "Kenny prefers Qwen 2.5 72B"
├─ Fact consolidation: Merging duplicates
├─ Preference inference: Patterns from behavior
└─ Temporal awareness: Facts have timestamps

Layer 2: Integrated Models
├─ Aesthetic embeddings (CLIP space)
├─ Procedural patterns (workflows, habits)
├─ Semantic relationships (entity graphs)
└─ Preference vectors (aggregated preferences)
```

### Entity Extraction from Conversations

Use a two-phase approach:

**Phase 1: Rule-Based Extraction**
- Named Entity Recognition (NER) for people, tools, places
- Intent detection for preference signals
- Topic extraction for domain tagging

**Phase 2: LLM Consolidation**
```python
import ollama
import json

def extract_facts(conversation_text: str) -> list[dict]:
    """Use LLM to extract salient facts from conversation"""
    prompt = f"""Extract salient facts, preferences, and entities from this conversation.
Output JSON with: entities, facts, preferences, topics.

Conversation:
{conversation_text[:4000]}
"""

    response = ollama.generate(
        model='qwen2.5:72b',
        prompt=prompt,
        format='json'
    )

    return json.loads(response['response'])
```

**Key Entities to Extract:**
- Tools/Technologies: "Uses MLX for Apple Silicon"
- Preferences: "Likes concise explanations"
- Domains: "Interested in personal AI systems"
- Temporal: "Works on DAEMON project currently"
- Relationships: "Tho is predecessor to DAEMON"

### Building Preference Vectors

Combine multiple signal types:

```python
def build_preference_vector(signals: list[dict]) -> np.ndarray:
    """Combine explicit and implicit signals into preference vector"""

    # Weight signals by type
    weights = {
        'explicit_statement': 1.0,   # "I prefer X"
        'tool_selection': 0.8,       # Chose to use X
        'time_spent': 0.6,           # Engaged longer with X
        'revisit_pattern': 0.7,      # Came back to X
        'bookmark': 0.5              # Saved X for later
    }

    weighted_vectors = []
    for signal in signals:
        weight = weights.get(signal['type'], 0.5)
        weight *= decay_by_age(signal['timestamp'])  # Recent = higher weight
        weighted_vectors.append((signal['embedding'], weight))

    # Weighted average
    return weighted_average(weighted_vectors)
```

### Deduplication and Conflict Resolution

**Problem:** Same fact expressed differently across sources

**Solution: Three-Stage Reconciliation**

```python
def deduplicate_fact(new_fact: dict, existing_memories: list) -> str:
    """Handle duplicate or conflicting facts"""

    # Stage 1: Vector similarity check
    similar = find_similar(new_fact['embedding'], existing_memories, threshold=0.85)

    if not similar:
        return 'add_new'

    # Stage 2: Semantic comparison
    if is_same_fact_semantically(new_fact, similar[0]):
        # Stage 3: Temporal handling
        if new_fact['timestamp'] > similar[0]['timestamp']:
            return 'update_existing'  # Newer version
        else:
            return 'skip'  # Already have newer
    else:
        return 'add_new'  # Different facts, both valid
```

**Evolution Chains:**
For facts that change over time:
```python
# Example: Model preference evolving
memory = {
    'fact': 'Prefers Qwen 2.5 72B for main reasoning',
    'supersedes': 'Previously used Hermes 3',
    'confidence': 0.92,
    'timestamp': '2025-12-24'
}
```

---

## 4. Aesthetic Memory: Image Embeddings

### CLIP Pipeline

Use CLIP to embed images into a semantic space where:
- Similar images cluster together
- Text descriptions align with image embeddings
- Aesthetic properties (lighting, composition) are encoded

```python
import clip
import torch
from PIL import Image

# Load model (once)
device = "mps" if torch.backends.mps.is_available() else "cpu"
model, preprocess = clip.load("ViT-L/14", device=device)

def embed_image(image_path: str) -> np.ndarray:
    """Generate CLIP embedding for image"""
    image = Image.open(image_path)
    image_input = preprocess(image).unsqueeze(0).to(device)

    with torch.no_grad():
        features = model.encode_image(image_input)
        features /= features.norm(dim=-1, keepdim=True)

    return features.cpu().numpy().flatten()
```

### Aesthetic Properties Captured

CLIP embeddings encode:
- **Lighting and contrast** - moody vs. bright
- **Color harmony** - saturated vs. muted
- **Composition** - balanced vs. asymmetric
- **Texture** - smooth vs. detailed
- **Subject matter** - abstract vs. figurative
- **Style** - minimalist vs. ornate

### Building Aesthetic Preferences

```python
def build_aesthetic_profile(image_sources: list) -> dict:
    """Build aesthetic preference from images user likes"""

    embeddings = []

    for source in image_sources:
        if source['type'] == 'saved_image':
            # High signal: user explicitly saved this
            embeddings.append((embed_image(source['path']), 1.0))

        elif source['type'] == 'screenshot':
            # Medium signal: user captured this
            embeddings.append((embed_image(source['path']), 0.7))

        elif source['type'] == 'created':
            # Highest signal: user made this
            embeddings.append((embed_image(source['path']), 1.2))

    # Compute preference centroid
    preference_vector = weighted_average(embeddings)

    # Find canonical examples (closest to preference)
    canonical = find_nearest(preference_vector, [e[0] for e in embeddings], k=5)

    return {
        'preference_vector': preference_vector,
        'canonical_examples': canonical,
        'source_count': len(embeddings)
    }
```

---

## 5. Privacy Filtering

### Categories to Filter

| Category | Detection Method | Action |
|----------|------------------|--------|
| PII (SSN, credit cards) | Regex patterns | Redact or skip |
| Health data | Keywords (diagnosis, medication) | Skip |
| Financial details | Account number patterns | Redact |
| Family/personal | Named entity detection | Skip |
| Credentials | Context patterns | Skip |
| Third-party data | Mentions of others | Review |

### Three-Stage Filter Pipeline

**Stage 1: Pattern Detection**
```python
import re

SENSITIVE_PATTERNS = {
    'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
    'credit_card': r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
    'phone': r'\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
}

def detect_patterns(text: str) -> list[str]:
    """Find sensitive patterns in text"""
    findings = []
    for name, pattern in SENSITIVE_PATTERNS.items():
        if re.search(pattern, text):
            findings.append(name)
    return findings
```

**Stage 2: Semantic Classification**
```python
def classify_sensitivity(text: str) -> dict:
    """Use LLM to detect sensitive content"""
    prompt = f"""Classify if this text contains sensitive personal information.
Output JSON: {{"has_sensitive": bool, "categories": [list], "confidence": float}}

Text: {text[:2000]}
"""
    response = ollama.generate(
        model='hermes3:latest',
        prompt=prompt,
        temperature=0.1  # Low temp for safety
    )
    return json.loads(response['response'])
```

**Stage 3: User Allowlist**
```python
PRIVACY_CONFIG = {
    'include_calendar_titles': True,
    'include_email_subjects': False,
    'include_financial_data': False,
    'include_health_data': False,
    'include_third_party': False,
    'custom_filters': [
        'internal company projects',
        'client names',
    ]
}
```

### Redaction for Partial Ingestion

When content is valuable but contains some sensitive elements:

```python
import spacy

nlp = spacy.load('en_core_web_sm')

def redact_text(text: str) -> str:
    """Redact sensitive elements while preserving semantic meaning"""

    # Redact phone numbers
    text = re.sub(SENSITIVE_PATTERNS['phone'], '[PHONE]', text)

    # Redact names
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ == 'PERSON':
            text = text.replace(ent.text, '[PERSON]')

    return text
```

---

## 6. Implementation Patterns

### Bootstrap vs. Continuous Sync

| Aspect | Bootstrap (One-Time) | Continuous Sync |
|--------|---------------------|-----------------|
| Initial cost | High | Low |
| Freshness | Stale until re-run | Always current |
| Complexity | Simpler | State management needed |
| Memory usage | Peak high, then stable | Gradually growing |

**Recommendation:** Bootstrap first, then add sync.

### Bootstrap Implementation

```python
from mem0 import Memory
from pathlib import Path

def bootstrap_memory(config: dict):
    """One-time memory initialization"""

    mem0 = Memory(config=MEM0_CONFIG)

    # Source 1: Claude conversations
    if config.get('claude_export'):
        for conv in extract_conversations(config['claude_export']):
            facts = extract_facts(conv['messages'])
            for fact in facts:
                mem0.add(fact['text'], metadata={
                    'source': 'claude',
                    'date': conv['created']
                })

    # Source 2: Obsidian notes
    if config.get('obsidian_vault'):
        for note in extract_obsidian(config['obsidian_vault']):
            if passes_privacy_filter(note['content']):
                facts = extract_facts(note['content'])
                for fact in facts:
                    mem0.add(fact['text'], metadata={
                        'source': 'obsidian',
                        'path': note['path'],
                        'tags': note.get('tags', [])
                    })

    # Source 3: Images for aesthetic memory
    if config.get('image_folders'):
        aesthetic = build_aesthetic_profile(
            scan_images(config['image_folders'])
        )
        store_aesthetic_memory(aesthetic)

    print(f"Bootstrap complete: {mem0.count()} memories")
```

### Continuous Sync Implementation

```python
from datetime import datetime

def continuous_sync(state: dict) -> dict:
    """Incremental memory updates"""

    last_sync = state.get('last_sync')

    # Detect new data
    new_convs = query_claude_api(since=last_sync)
    modified_notes = scan_obsidian_mtimes(since=last_sync)

    # Process incrementally
    for conv in new_convs:
        facts = extract_facts(conv)
        for fact in facts:
            # Check for duplicates before adding
            if not exists_in_memory(fact):
                mem0.add(fact['text'], metadata=fact['metadata'])

    # Update state
    state['last_sync'] = datetime.now().isoformat()
    return state
```

### Verification Workflow

After ingestion, verify quality:

```python
def verify_memory_quality():
    """Spot-check ingested memories"""

    # Query 1: General preferences
    prefs = mem0.search("What are the user's preferences?", limit=10)
    print("Preferences found:", len(prefs))

    # Query 2: Active projects
    projects = mem0.search("What projects is the user working on?", limit=5)
    print("Projects found:", len(projects))

    # Query 3: Aesthetic (if images ingested)
    if aesthetic_memory:
        print("Aesthetic examples:", len(aesthetic_memory['canonical_examples']))

    # Interactive review
    for pref in prefs[:5]:
        print(f"- {pref['text'][:100]}...")
```

---

## 7. Complete Example: Ingestion Script

```python
#!/usr/bin/env python3
"""
DAEMON Memory Bootstrap Script
Usage: python bootstrap.py --config config.yaml
"""

import argparse
import yaml
from pathlib import Path
from datetime import datetime
from mem0 import Memory
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mem0 configuration for fully local operation
MEM0_CONFIG = {
    "llm": {
        "provider": "ollama",
        "config": {
            "model": "qwen2.5:72b",
            "temperature": 0.3,
        }
    },
    "embedder": {
        "provider": "ollama",
        "config": {
            "model": "nomic-embed-text",
        }
    },
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "collection_name": "daemon-memory",
            "path": "./daemon-memory-db",
        }
    }
}

def main():
    parser = argparse.ArgumentParser(description="Bootstrap DAEMON memory")
    parser.add_argument('--config', required=True, help='Config YAML file')
    parser.add_argument('--dry-run', action='store_true', help='Parse without storing')
    args = parser.parse_args()

    with open(args.config) as f:
        config = yaml.safe_load(f)

    mem0 = Memory(config=MEM0_CONFIG)
    stats = {'conversations': 0, 'notes': 0, 'images': 0, 'filtered': 0}

    # Process each source
    if config.get('claude_export'):
        logger.info("Processing Claude conversations...")
        for conv in extract_conversations(Path(config['claude_export'])):
            if passes_privacy_filter(conv):
                facts = extract_facts(conv['messages'])
                for fact in facts:
                    if not args.dry_run:
                        mem0.add(fact['text'], metadata={'source': 'claude'})
                    stats['conversations'] += 1
            else:
                stats['filtered'] += 1

    if config.get('obsidian_vault'):
        logger.info("Processing Obsidian vault...")
        for note in extract_obsidian(config['obsidian_vault']):
            if passes_privacy_filter(note['content']):
                facts = extract_facts(note['content'])
                for fact in facts:
                    if not args.dry_run:
                        mem0.add(fact['text'], metadata={'source': 'obsidian'})
                    stats['notes'] += 1
            else:
                stats['filtered'] += 1

    if config.get('image_folders'):
        logger.info("Processing images for aesthetic memory...")
        for folder in config['image_folders']:
            images = list(Path(folder).glob('**/*.{png,jpg,jpeg,webp}'))
            stats['images'] += len(images)
            if not args.dry_run:
                aesthetic = build_aesthetic_profile([
                    {'path': str(img), 'type': 'saved_image'}
                    for img in images
                ])
                store_aesthetic_memory(aesthetic)

    # Log results
    logger.info(f"Bootstrap complete:")
    logger.info(f"  Conversations: {stats['conversations']}")
    logger.info(f"  Notes: {stats['notes']}")
    logger.info(f"  Images: {stats['images']}")
    logger.info(f"  Filtered: {stats['filtered']}")

    if not args.dry_run:
        logger.info(f"  Total memories: {mem0.count()}")

    # Save ingestion log
    with open('ingestion_log.json', 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'stats': stats,
            'config': config
        }, f, indent=2)

if __name__ == '__main__':
    main()
```

**Example config.yaml:**
```yaml
# DAEMON Memory Bootstrap Configuration

claude_export: ~/Downloads/claude_export.json
obsidian_vault: ~/Obsidian Vault

image_folders:
  - ~/Pictures/Inspiration
  - ~/Desktop/Screenshots

privacy:
  include_calendar: false
  include_email: false
  include_health: false
  custom_filters:
    - client names
    - internal projects
```

---

## 8. Summary and Next Steps

### Implementation Phases

**Phase 1: Setup (Days 1-2)**
- Install Ollama + nomic-embed-text + qwen2.5:72b
- Install Qdrant (Docker or standalone)
- Install Mem0 Python SDK
- Gather exports (Claude, Obsidian, images)

**Phase 2: Ingestion (Days 3-7)**
- Build extraction scripts
- Test on sample data
- Run full ingestion with privacy filters
- Verify memory quality

**Phase 3: Integration (Days 8+)**
- Connect to DAEMON orchestrator
- Test conversation flow with memories
- Set up continuous sync
- Iterate based on usage

### Key Takeaways

1. **Multi-source ingestion** provides richer context than any single source
2. **Privacy filters** must be aggressive—better to miss data than leak it
3. **Deduplication matters**—same facts expressed differently will clutter memory
4. **Bootstrap first, then sync**—get historical data in before worrying about continuous updates
5. **Verification is critical**—test memory queries before relying on them

### References

- [Mem0 Documentation](https://docs.mem0.ai/)
- [Qdrant Bulk Upload Guide](https://qdrant.tech/documentation/database-tutorials/bulk-upload/)
- [CLIP for Image Understanding](https://openai.com/research/clip)
- [obsidianmd-parser](https://codeberg.org/paddyd/obsidianmd-parser)
- [Claude Conversation Extractor](https://github.com/ZeroSumQuant/claude-conversation-extractor)

---

*This guide completes the DAEMON research documentation suite, providing the "cold start" solution for bootstrapping memory from existing data.*
