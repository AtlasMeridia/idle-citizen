# researchscan

R&D research aggregator for AI/ML developments. Collects and stores papers from arXiv and trending models from HuggingFace in a SQLite database for browsing and analysis.

Built as a prototype for DAEMON's R&D Agent component.

## Features

- **arXiv collector**: Fetches recent papers from cs.CL, cs.LG, cs.AI, cs.CV
- **HuggingFace collector**: Fetches trending models for text-generation, ASR, TTS, image-to-text
- **Relevance scoring**: Papers are scored by keyword relevance to local AI development
- **Search**: Full-text search across paper titles and summaries
- **Digest generation**: Markdown summary of high-relevance papers and top models

## Installation

Requires Python 3.7+. The HuggingFace collector is optional:

```bash
# For full functionality
pip install huggingface_hub

# arXiv collector works with stdlib only
```

## Usage

```bash
# Collect from all sources
python researchscan.py collect

# Collect from specific source
python researchscan.py collect arxiv
python researchscan.py collect hf

# List papers (sorted by relevance)
python researchscan.py papers --relevant

# List top models
python researchscan.py models
python researchscan.py models --task text-generation

# Search papers
python researchscan.py search "quantization"
python researchscan.py search "agent memory"

# View statistics
python researchscan.py stats

# Show new papers since last check
python researchscan.py new              # Shows new papers, marks as read
python researchscan.py new --no-mark    # Shows new papers without marking

# Generate markdown digest
python researchscan.py digest --days 7
```

## Daily Workflow

```bash
# Morning routine: collect and review new papers
python researchscan.py collect
python researchscan.py new

# Or combine in one line
python researchscan.py collect && python researchscan.py new
```

## Relevance Keywords

Papers are scored based on matches to keywords relevant to local AI development:

- Local inference: `local`, `efficient`, `quantization`, `gguf`, `ggml`
- Apple Silicon: `mlx`, `m1`, `m2`, `m3`, `m4`, `apple silicon`
- Memory systems: `memory`, `retrieval`, `rag`, `embedding`, `vector`
- Agents: `agent`, `agents`, `personalization`, `personal`
- Models: `llama`, `mistral`, `phi`, `qwen`, `gemma`, `ollama`
- Fine-tuning: `lora`, `qlora`, `adapter`, `fine-tuning`
- Speech: `voice`, `speech`, `whisper`, `tts`, `stt`

## Database

Data is stored in `researchscan.db` (SQLite). Can be browsed with Datasette:

```bash
pip install datasette
datasette researchscan.db
```

## Categories

**arXiv categories monitored:**
- `cs.CL` — Computation and Language (NLP, LLMs)
- `cs.LG` — Machine Learning
- `cs.AI` — Artificial Intelligence
- `cs.CV` — Computer Vision (multimodal)

**HuggingFace tasks monitored:**
- `text-generation` — LLM models
- `automatic-speech-recognition` — STT models
- `text-to-speech` — TTS models
- `image-to-text` — Vision-language models

## Future Extensions

- Reddit r/LocalLLaMA collector (requires PRAW + credentials)
- GitHub release monitoring (requires token)
- Automated weekly digest generation
- LLM-powered paper summarization
- Integration with DAEMON memory system
