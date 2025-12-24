# DAEMON Local Vision-Language Models Implementation Guide

*Research for Phase 2 (Perception) of DAEMON — enabling visual understanding capabilities.*

**Created:** 2025-12-24
**Status:** Research complete, ready for implementation

---

## Executive Summary

Local vision-language models (VLMs) have matured significantly in 2024-2025, making it practical to run capable multimodal AI entirely on Apple Silicon. For DAEMON's vision module, **Qwen2.5-VL** is the recommended model family, run via **MLX-VLM** on Mac.

**Key recommendations:**
- **Primary model:** Qwen2.5-VL-7B-Instruct (4-bit quantized) for balanced performance
- **Lightweight option:** Qwen2.5-VL-2B-Instruct for faster response times
- **Framework:** MLX-VLM for native Apple Silicon optimization
- **Capabilities:** Image understanding, document analysis, UI navigation, video processing

---

## Model Landscape (December 2025)

### Top Tier Open Source VLMs

| Model | Sizes | Strengths | Local Feasibility |
|-------|-------|-----------|-------------------|
| **Qwen2.5-VL** | 2B, 7B, 32B, 72B | All-rounder, agentic, math, UI navigation | Excellent on Mac |
| **Gemma 3** | 4B, 12B, 27B | 128k context, 140+ languages, video | Good on Mac |
| **Kimi-VL-Thinking** | 16B MoE (3B active) | Best reasoning, long chain-of-thought | Moderate |
| **SmolVLM2** | 256M, 500M, 2.2B | Smallest VLM, device-friendly | Excellent |
| **LLaVA 1.6** | 7B, 13B, 34B | Pioneer architecture, widely supported | Good |

### Architecture Evolution

VLMs combine three components:
1. **Vision encoder** — Extracts image features (usually CLIP ViT or SigLIP)
2. **Projector/adapter** — Maps vision features to language model space (MLP now standard)
3. **Language model** — Generates text responses (Qwen, Llama, etc.)

The trend has been toward simpler architectures (MLP adapters) with larger training datasets. Qwen2.5-VL uses "Native Resolution ViT" allowing dynamic input resolutions.

---

## Recommended Stack for DAEMON

### Primary Choice: Qwen2.5-VL via MLX-VLM

**Why Qwen2.5-VL:**
- Outperforms LLaVA and most open-source competitors on benchmarks
- Native support for document understanding, mathematical reasoning
- Agentic capabilities (UI navigation, device control)
- Video processing up to 20+ minutes
- Active development from Alibaba team

**Why MLX-VLM:**
- Native Apple Silicon optimization (Metal backend)
- 3x faster model loading than llama.cpp
- 26-30% higher token generation speeds
- Pre-quantized models available (4-bit, 8-bit)
- OpenAI-compatible API server built-in

### Installation

```bash
# Install MLX-VLM
pip install -U mlx-vlm

# Test basic inference
mlx_vlm.generate \
  --model mlx-community/Qwen2.5-VL-7B-Instruct-4bit \
  --max-tokens 200 \
  --prompt "Describe this image in detail" \
  --image /path/to/image.jpg
```

### Python Integration

```python
from mlx_vlm import load, generate
from mlx_vlm.utils import load_image

# Load model (one-time, cache for session)
model, processor = load("mlx-community/Qwen2.5-VL-7B-Instruct-4bit")

# Prepare prompt with image
messages = [
    {
        "role": "user",
        "content": [
            {"type": "image", "image": "/path/to/image.jpg"},
            {"type": "text", "text": "What do you see in this image?"}
        ]
    }
]

# Apply chat template
formatted_prompt = processor.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True
)

# Generate response
output = generate(
    model,
    processor,
    formatted_prompt,
    image="/path/to/image.jpg",
    max_tokens=500
)
print(output)
```

### OpenAI-Compatible Server

MLX-VLM includes a FastAPI server for integration:

```bash
# Start server
mlx_vlm.server --model mlx-community/Qwen2.5-VL-7B-Instruct-4bit

# Call via OpenAI SDK
from openai import OpenAI
client = OpenAI(base_url="http://localhost:8000/v1", api_key="none")

response = client.chat.completions.create(
    model="mlx-community/Qwen2.5-VL-7B-Instruct-4bit",
    messages=[{
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {"url": "file:///path/to/image.jpg"}},
            {"type": "text", "text": "Describe this image"}
        ]
    }]
)
```

---

## Memory Requirements

### Model Size vs RAM

| Model | Quantization | ~RAM Required | Speed (M4 Max) |
|-------|--------------|---------------|----------------|
| Qwen2.5-VL-2B | 4-bit | ~2 GB | Very fast |
| Qwen2.5-VL-7B | 4-bit | ~5 GB | ~35 tok/s |
| Qwen2.5-VL-7B | 8-bit | ~9 GB | ~25 tok/s |
| Qwen2.5-VL-32B | 4-bit | ~20 GB | Moderate |

### Hardware Recommendations

| Mac Config | Recommended Model | Notes |
|------------|-------------------|-------|
| 16GB RAM | Qwen2.5-VL-7B-4bit | Sweet spot for most use cases |
| 32GB RAM | Qwen2.5-VL-7B-8bit or 32B-4bit | Higher quality or larger model |
| 64GB+ RAM | Full range | Can run multiple models |

Leave 4-8GB for system and other applications. Unified memory architecture means GPU uses same pool.

---

## Capabilities for DAEMON

### 1. Camera/Screen Analysis

DAEMON's Phase 2 requirement: "What am I looking at?"

```python
# Screenshot analysis
import subprocess

def capture_screen():
    subprocess.run(["screencapture", "-x", "/tmp/screen.png"])
    return "/tmp/screen.png"

def analyze_screen():
    image_path = capture_screen()
    messages = [{
        "role": "user",
        "content": [
            {"type": "image", "image": image_path},
            {"type": "text", "text": "Describe what's on this screen. Focus on the main content and any notable UI elements."}
        ]
    }]
    # ... generate response
```

### 2. Document Understanding

Qwen2.5-VL excels at document QA (DocVQA benchmark leader):

```python
messages = [{
    "role": "user",
    "content": [
        {"type": "image", "image": "/path/to/document.pdf"},  # or screenshot
        {"type": "text", "text": "Summarize the key points in this document."}
    ]
}]
```

### 3. Creative Work Analysis

Building DAEMON's aesthetic memory:

```python
def analyze_aesthetic(image_paths, prompt):
    """Analyze images to extract aesthetic preferences."""
    content = []
    for path in image_paths:
        content.append({"type": "image", "image": path})
    content.append({
        "type": "text",
        "text": prompt or "Describe the visual style, mood, color palette, and composition of these images. What aesthetic sensibilities do they share?"
    })

    messages = [{"role": "user", "content": content}]
    # ... generate and store in aesthetic memory
```

### 4. UI Navigation (Agentic)

Qwen2.5-VL can identify and locate UI elements:

```python
messages = [{
    "role": "user",
    "content": [
        {"type": "image", "image": "/tmp/screen.png"},
        {"type": "text", "text": "Find the 'Submit' button and tell me its location on screen."}
    ]
}]
```

### 5. Video Understanding

Process video files (extracts frames automatically):

```bash
mlx_vlm.generate \
  --model mlx-community/Qwen2.5-VL-7B-Instruct-4bit \
  --video /path/to/video.mp4 \
  --prompt "Summarize what happens in this video"
```

---

## Integration with DAEMON Architecture

### Module Interface

```python
class VisionModule:
    """DAEMON Vision perception module using Qwen2.5-VL."""

    def __init__(self, model_name="mlx-community/Qwen2.5-VL-7B-Instruct-4bit"):
        from mlx_vlm import load
        self.model, self.processor = load(model_name)

    def describe(self, image_path: str, context: str = "") -> str:
        """General image description."""
        ...

    def analyze_screen(self) -> dict:
        """Capture and analyze current screen."""
        ...

    def extract_text(self, image_path: str) -> str:
        """OCR-like text extraction."""
        ...

    def compare_aesthetics(self, images: list[str]) -> dict:
        """Compare visual styles for preference learning."""
        ...

    def find_element(self, image_path: str, description: str) -> dict:
        """Locate UI element by description."""
        ...
```

### Hot-Swapping Support

DAEMON's principle: modules should be replaceable. VLM module should:

1. Expose consistent interface regardless of underlying model
2. Load model lazily (on first request)
3. Support model switching without restart (unload/reload)
4. Gracefully degrade if model unavailable

```python
class VisionModule:
    def switch_model(self, new_model: str):
        """Hot-swap to a different model."""
        self.unload()
        self.model, self.processor = load(new_model)

    def unload(self):
        """Free memory."""
        del self.model
        del self.processor
        import gc
        gc.collect()
```

---

## Alternative Options

### SmolVLM2 for Speed

If response time is critical:

```bash
pip install -U mlx-vlm
mlx_vlm.generate --model HuggingFaceTB/SmolVLM2-500M-Instruct ...
```

~500M parameters, runs on any Apple Silicon Mac, very fast but less capable.

### LLaVA via Ollama

If already using Ollama for LLM:

```bash
ollama run llava:13b
```

Simpler integration but less optimized than MLX on Mac.

### Gemma 3 for Long Context

If processing long videos or documents:
- 128k context window
- 140+ language support
- Available via MLX

---

## Performance Benchmarks

### Qwen2.5-VL-7B on Apple Silicon

| Resolution | M4 Max (128GB) Speed |
|------------|---------------------|
| 336×336 | ~68 tok/s |
| 672×672 | ~45 tok/s |
| 1344×1344 | ~25 tok/s |
| 1920×1080 | ~14 tok/s |

Higher resolution = slower but more detail captured.

### Startup Time

- MLX model load: <10 seconds
- llama.cpp equivalent: ~30 seconds

---

## Implementation Checklist for DAEMON

### Phase 2.1: Basic Vision

- [ ] Install MLX-VLM
- [ ] Test Qwen2.5-VL-7B-4bit inference
- [ ] Create VisionModule class with consistent interface
- [ ] Implement screen capture integration
- [ ] Add "What am I looking at?" query capability

### Phase 2.2: Creative Analysis

- [ ] Implement multi-image aesthetic comparison
- [ ] Create aesthetic preference extraction prompts
- [ ] Store analyzed preferences in DAEMON's Aesthetic Memory
- [ ] Build reference retrieval ("find things like this")

### Phase 2.3: Document Understanding

- [ ] Test PDF/document screenshot analysis
- [ ] Integrate with File Watcher module for creative work detection
- [ ] Add summarization for long documents

### Phase 2.4: Video Support

- [ ] Test video file processing
- [ ] Implement frame selection optimization
- [ ] Add temporal query support ("what happens at 2:30?")

---

## References

- [MLX-VLM GitHub](https://github.com/Blaizzy/mlx-vlm) — Primary framework
- [Qwen2.5-VL Model Card](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct) — Model documentation
- [Vision Language Models (2025 Overview)](https://huggingface.co/blog/vlms-2025) — Comprehensive landscape
- [Apple FastVLM Research](https://machinelearning.apple.com/research/fast-vision-language-models) — Apple's VLM optimizations
- [QwenVL vs LLaVA Comparison](https://roboflow.com/compare/qwenvl-vs-llava) — Benchmark comparison
- [vLLM-MLX](https://github.com/waybarrios/vllm-mlx) — Alternative server implementation
- [MLX-VLM Practical Guide](https://dzone.com/articles/vision-ai-apple-silicon-guide-mlx-vlm) — Tutorial walkthrough
- [VLM Design Choices (2024)](https://huggingface.co/blog/gigant/vlm-design) — Architecture analysis

---

*This research completes the vision perception component of DAEMON's Phase 2. Combined with the speech recognition (Session 9) and TTS (Session 25) research, DAEMON now has documented paths for full multimodal perception and output.*
