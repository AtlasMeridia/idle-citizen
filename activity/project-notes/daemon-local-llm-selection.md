# DAEMON Local LLM Selection Guide

*Research for DAEMON Project Phase 1: Foundation*

**Created:** 2025-12-24
**Purpose:** Recommend optimal local LLM models for DAEMON's core reasoning module

---

## Overview

DAEMON requires a local LLM for its "Core Daemon (Orchestrator)" that can:
- Hold natural conversations with personality consistency
- Integrate with memory systems (Mem0)
- Run efficiently on Apple Silicon (Mac Studio M2 Ultra with 192GB RAM as reference)
- Support tool-use and function calling
- Handle long context for memory injection

This guide covers model selection, inference frameworks, and optimization recommendations.

---

## Recommended Models

### Primary Recommendation: Qwen 2.5 72B

**Why Qwen 2.5:**
- Excellent structured data handling (critical for memory integration)
- Strong multilingual support (29+ languages)
- Outstanding performance on MMLU and MATH benchmarks
- Available in multiple sizes: 0.5B to 72B
- Specialized variants (Coder, Math) available for specific tasks
- Apache 2.0 license allows commercial use

**For 192GB RAM (Mac Studio M2 Ultra):**
- Run `qwen2.5:72b` comfortably with room for memory system overhead
- Or use `qwen2.5:32b` with larger context windows

**Considerations:**
- Can sound formal in creative contexts — use style anchors in personality prompts
- Dense architecture means slower than MoE alternatives at same parameter count

### Secondary Option: DeepSeek R1 Distilled

**Why DeepSeek R1:**
- State-of-the-art reasoning capabilities (chain-of-thought)
- 69.8% accuracy on AIME mathematics benchmark (14B model)
- MIT License — fully open for commercial use and modification
- Multiple distilled sizes: 1.5B, 7B, 8B, 14B, 32B, 70B

**Recommended Size:**
- `deepseek-r1:32b` — runs well on 32GB+ RAM, excellent balance
- `deepseek-r1:14b` — viable on 16GB RAM machines for lighter workloads

**Considerations:**
- Thinking tokens visible in output (may need post-processing for clean responses)
- Best for tasks requiring explicit reasoning chains
- Qwen-based distills may be better quality than Llama-based distills

### For Faster Inference: Llama 3.3 70B

**Why Llama 3.3:**
- Excellent instruction following ("if you say 5 bullets, you get 5 bullets")
- Lower latency and higher throughput than alternatives
- Strong coding performance (HumanEval, MBPP)
- Natural conversational tone

**Considerations:**
- Slightly weaker on structured data than Qwen
- Good fallback if Qwen feels too formal for companion interaction

---

## Inference Frameworks

### Production Recommendation: MLX

**Why MLX for DAEMON:**
- Highest sustained generation throughput on Apple Silicon
- Native unified memory utilization
- Metal/GPU optimization without configuration
- Seamless Swift integration for future native app development
- Deep Apple ecosystem integration

**Performance Notes:**
- MLX achieves highest throughput in benchmarks vs Ollama, llama.cpp, MLC-LLM
- MLX models often perform better than equivalent GGUF quantizations

**Downsides:**
- Less ecosystem support than Ollama
- Apple-only (not an issue for DAEMON)

### Development Alternative: Ollama

**Why Ollama for prototyping:**
- "Developer ergonomics" — easy setup and management
- CLI-friendly for scripting and automation
- Wide model availability
- OpenAI-compatible API for easy integration

**Performance Notes:**
- Trails MLX in throughput and time-to-first-token (TTFT)
- Built on llama.cpp — highly efficient for single-stream use
- Better for headless/background processes

### Recommended Approach

1. **Start with Ollama** for rapid prototyping and validation
2. **Migrate to MLX** for production deployment
3. **Use LM Studio** for GUI-based testing (MLX backend available)

---

## Memory Requirements

### Model Size Guidelines for Apple Silicon

| Model Size | Minimum RAM | Comfortable | Notes |
|------------|-------------|-------------|-------|
| 7B-8B | 8GB | 16GB | Basic tasks, mobile |
| 14B | 16GB | 32GB | Good reasoning, slower on 16GB |
| 32B | 32GB | 64GB | Excellent balance |
| 70B-72B | 64GB | 128GB+ | Full capability |

**Rule of thumb:** Subtract ~8GB from total RAM for OS overhead. Remaining memory determines max model size.

**DAEMON Target (192GB RAM):**
- Run 72B models with ample headroom
- Room for memory system (Mem0 + Qdrant) in parallel
- Large context windows (32K-128K tokens) without swapping

---

## Quantization Recommendations

### Best Quality: 4-bit OmniQuant/GPTQ

Research shows OmniQuant and GPTQ quantized models outperform standard Q4_K_M GGUF quantizations used by llama.cpp-based tools.

### Pragmatic Choice: Q4_K_M GGUF

- Wide compatibility (Ollama, LM Studio, llama.cpp)
- Good quality/size balance
- Easy to switch models

### For MLX: Native 4-bit RTN

- MLX has its own quantization format
- Often better quality than equivalent GGUF
- Check mlx-community on HuggingFace for pre-quantized models

---

## Context Length Considerations

DAEMON's memory injection requires generous context windows:

| Use Case | Recommended Context | Notes |
|----------|---------------------|-------|
| Basic conversation | 8K tokens | Minimal memory injection |
| With episodic memory | 16K-32K tokens | Recent history + facts |
| Full memory integration | 64K-128K tokens | Comprehensive context |

**Model Context Support:**
- Qwen 2.5: Up to 128K native
- DeepSeek R1: 128K supported
- Llama 3.3: 128K supported

---

## Tool-Use and Function Calling

DAEMON requires tool-use for:
- Memory read/write operations
- File system access
- Web search (R&D agent)
- Image generation triggers

**Best tool-use support:**
1. **Qwen 2.5** — Excellent structured output, JSON handling
2. **Llama 3.3** — Strong instruction following
3. **DeepSeek R1** — Good but may require prompt engineering

**Recommendation:** Use Qwen 2.5 for the main orchestrator due to superior structured data handling, which translates to more reliable tool calls.

---

## Specific Configuration for DAEMON

### Phase 1 Setup (Recommended)

```yaml
# daemon_llm_config.yaml
primary_model:
  name: qwen2.5:72b-instruct
  framework: ollama  # Start here, migrate to MLX
  context_length: 32768
  temperature: 0.7
  top_p: 0.9

fallback_model:
  name: qwen2.5:32b-instruct
  framework: ollama
  context_length: 65536

reasoning_model:
  name: deepseek-r1:32b
  framework: ollama
  use_for: ["complex_analysis", "math", "code_review"]

embedding_model:
  name: nomic-embed-text
  framework: ollama
  dimensions: 768
```

### Model Routing Strategy

```
Conversation → Qwen 2.5 72B (personality, memory integration)
Complex reasoning → DeepSeek R1 32B (explicit thinking)
Embeddings → Nomic Embed (memory storage/retrieval)
Quick responses → Qwen 2.5 14B (low latency fallback)
```

---

## Performance Benchmarks (Reference)

From [arXiv:2511.05502](https://arxiv.org/abs/2511.05502) testing on Mac Studio M2 Ultra:

| Framework | Throughput | TTFT | Notes |
|-----------|------------|------|-------|
| MLX | Highest | Moderate | Best for sustained generation |
| MLC-LLM | High | Lowest | Best for interactive use |
| llama.cpp | Moderate | Moderate | Lightweight, single-stream |
| Ollama | Lower | Higher | Developer-friendly |

---

## Migration Path

### Current → Production

1. **Now:** Use Ollama + Qwen 2.5 32B for initial development
2. **Validation:** Test with full 72B model once core loop works
3. **Optimization:** Migrate to MLX for production deployment
4. **Future:** Evaluate new models as R&D agent surfaces them

---

## Sources

- [Top 5 Local LLM Tools and Models 2025](https://pinggy.io/blog/top_5_local_llm_tools_and_models_2025/)
- [MLX vs Ollama Comparison](https://www.markus-schall.de/en/2025/09/mlx-auf-apple-silicon-als-lokale-ki-im-vergleich-mit-ollama-co/)
- [arXiv: Production-Grade Local LLM Inference on Apple Silicon](https://arxiv.org/abs/2511.05502)
- [DeepSeek R1 on Ollama](https://ollama.com/library/deepseek-r1)
- [Qwen 2.5 vs Llama 3.3 Comparison](https://blogs.novita.ai/qwen-2-5-72b-vs-llama-3-3-70b-which-model-suits-your-needs/)
- [Best Local LLMs for Apple Silicon](https://apxml.com/posts/best-local-llm-apple-silicon-mac)
- [DeepSeek R1 Distill on Private LLM](https://privatellm.app/blog/deepseek-r1-distill-now-available-private-llm-ios-macos)

---

## Summary

**For DAEMON Phase 1:**

| Component | Model | Framework | Size |
|-----------|-------|-----------|------|
| Primary LLM | Qwen 2.5 72B Instruct | Ollama → MLX | 72B |
| Reasoning | DeepSeek R1 Distilled | Ollama | 32B |
| Embeddings | Nomic Embed Text | Ollama | - |
| Quick fallback | Qwen 2.5 14B | MLX | 14B |

This configuration leverages Qwen's structured data handling for memory integration and tool use, DeepSeek R1's reasoning for complex tasks, and MLX's throughput for production deployment.
