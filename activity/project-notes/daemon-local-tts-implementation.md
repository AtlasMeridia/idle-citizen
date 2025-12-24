# Local Text-to-Speech for DAEMON

Research on self-hosted TTS options for DAEMON's voice-first AI companion.

---

## Summary

DAEMON needs voice synthesis that runs locally, minimizes latency, and supports voice customization. The field has matured significantly, with several production-ready options for Apple Silicon.

**Recommendation:** Start with **Kokoro via mlx-audio** for immediate Apple Silicon optimization, with **openedai-speech** as the API layer for OpenAI compatibility. This gives you the lowest-latency local option while maintaining API flexibility.

---

## Requirements for DAEMON

Based on the DAEMON intent doc:
- **Local-first**: No cloud dependencies
- **Low latency**: Voice companion needs responsive synthesis (<200ms to first audio)
- **Voice personality**: Consistent voice that matches DAEMON's configured personality
- **Streaming capable**: Support for real-time text chunk processing from LLM output
- **Apple Silicon optimized**: DAEMON runs on Kenny's Mac hardware

---

## Recommended Stack

### Primary: mlx-audio + Kokoro (Best for Apple Silicon)

[mlx-audio](https://github.com/Blaizzy/mlx-audio) is built specifically for Apple's MLX framework, providing native Metal acceleration.

**Key features:**
- Kokoro-82M: 82 million parameters, runs real-time on CPU
- On M1 MacBook Air: averages 0.7x real-time (CPU only)
- On M-series GPU: significantly faster
- MIT licensed, commercial use allowed

**Installation:**
```bash
pip install mlx-audio
```

**Usage:**
```python
from mlx_audio.tts.generate import generate_audio

generate_audio(
    text="Hello, I'm DAEMON.",
    model_path="prince-canuma/Kokoro-82M",
    voice="af_heart",  # female voice preset
    speed=1.0,
    lang_code="a"  # American English
)
```

**Voice presets:**
- `af_heart`, `af_nova`, `af_bella` — American female
- `bf_emma` — British female
- (More voices available)

**Why this for DAEMON:**
- Native Apple Silicon optimization via MLX
- No GPU setup complexity
- Real-time speed on CPU alone
- Easy integration with Python orchestration layer

---

### OpenAI-Compatible API: openedai-speech

For API compatibility (useful if DAEMON uses OpenAI-style endpoints):

[openedai-speech](https://github.com/matatonic/openedai-speech) wraps XTTS-v2 and Piper with an OpenAI-compatible `/v1/audio/speech` endpoint.

**Features:**
- Drop-in OpenAI TTS replacement
- Voices: alloy, echo, fable, onyx, nova, shimmer (mapped to local models)
- Formats: mp3, opus, aac, flac, wav, pcm
- Voice cloning via XTTS-v2 backend

**Docker setup:**
```bash
docker run -d -p 8000:8000 matatonic/openedai-speech
```

**Usage:**
```bash
curl -X POST http://localhost:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"model": "tts-1", "input": "Hello world!", "voice": "nova"}' \
  --output speech.mp3
```

**Why this for DAEMON:**
- Familiar OpenAI API for any code expecting that interface
- Easy to swap between local/cloud if needed
- XTTS-v2 backend supports voice cloning

---

### Alternative: Coqui TTS (XTTS-v2) Direct

The most feature-rich option if you need voice cloning:

**Installation:**
```bash
pip install coqui-tts  # Community fork, supports Python 3.12
```

**Voice cloning from 6-second sample:**
```python
from TTS.api import TTS

tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")

wav = tts.tts(
    text="Hello, this is my cloned voice.",
    speaker_wav="/path/to/6second_sample.wav",
    language="en"
)
```

**Key features:**
- 17 languages
- Voice cloning from 6-second audio
- Cross-language cloning (clone English voice, speak in Japanese)
- Emotion/style transfer from reference audio
- ~200ms latency with streaming

**Caveats:**
- Requires GPU for good performance (8GB+ VRAM recommended)
- Original Coqui AI shut down (Jan 2024), community fork continues
- Heavier resource requirements than Kokoro

---

## Streaming Text-to-Speech

For real-time voice output as LLM generates text:

### RealtimeTTS (Python)

[RealtimeTTS](https://github.com/KoljaB/RealtimeTTS) handles the stream-to-speech pipeline:

```python
from RealtimeTTS import TextToAudioStream, CoquiEngine

engine = CoquiEngine()
stream = TextToAudioStream(engine)

# Feed text chunks as they arrive from LLM
stream.feed("Hello, ")
stream.feed("this is ")
stream.feed("streaming text.")

# Play audio as it's synthesized
stream.play_async()
```

**Why this matters:**
- Traditional TTS waits for complete text
- Streaming TTS starts audio while text is still arriving
- Critical for voice companion responsiveness

---

## Comparison Matrix

| Solution | Latency | Voice Cloning | Apple Silicon | OpenAI API | GPU Required |
|----------|---------|---------------|---------------|------------|--------------|
| **mlx-audio + Kokoro** | ~0.7x RT | No | Native | No | No |
| **openedai-speech** | ~200ms | Yes (XTTS) | Via Docker | Yes | Optional |
| **Coqui TTS (XTTS-v2)** | ~200ms | Yes | Via Python | No | Recommended |
| **Piper** | Very fast | No | Limited | No | No |
| **RealtimeTTS** | Streaming | Depends on backend | Via backends | No | Depends |

---

## Architecture Recommendation for DAEMON

```
LLM Output (streaming text chunks)
        ↓
RealtimeTTS (manages chunk buffering)
        ↓
mlx-audio/Kokoro (synthesis on Apple Silicon)
        ↓
Audio Output (speaker/headphones)
```

**Phase 1: Start Simple**
- Install mlx-audio
- Use Kokoro with a preset voice matching DAEMON's personality
- Direct synthesis for complete responses

**Phase 2: Add Streaming**
- Integrate RealtimeTTS for chunk-by-chunk processing
- Reduce perceived latency significantly

**Phase 3: Voice Customization**
- If preset voices don't fit, use XTTS-v2 for voice cloning
- Record a 6-second sample of the desired voice
- Consider running XTTS-v2 via openedai-speech for API consistency

---

## Latency Considerations

The voice companion pipeline:
```
User speaks → STT → LLM processing → TTS → Audio output
```

Total latency = STT + LLM + TTS + audio buffering

**Target:** Under 1 second for complete pipeline

**TTS budget:** ~200ms to first audio byte

Options that hit this target:
- Kokoro on Apple Silicon: ~100-150ms (CPU)
- XTTS-v2 with streaming: ~150-200ms (GPU)
- Piper: <100ms (but lower quality)

---

## Quick Start

**Minimal setup (10 minutes):**

```bash
# 1. Install
pip install mlx-audio

# 2. Test
python -c "
from mlx_audio.tts.generate import generate_audio
generate_audio(
    text='Hello, I am DAEMON.',
    model_path='prince-canuma/Kokoro-82M',
    voice='af_heart',
    speed=1.0,
    lang_code='a'
)
"

# 3. Play the generated audio file
```

---

## Sources

- [mlx-audio](https://github.com/Blaizzy/mlx-audio) — Apple Silicon TTS library
- [Kokoro-82M](https://huggingface.co/prince-canuma/Kokoro-82M) — Lightweight TTS model
- [openedai-speech](https://github.com/matatonic/openedai-speech) — OpenAI-compatible TTS server
- [Coqui TTS / XTTS-v2](https://github.com/coqui-ai/TTS) — Voice cloning TTS
- [RealtimeTTS](https://github.com/KoljaB/RealtimeTTS) — Streaming TTS library
- [Best Self-Hosted TTS Models 2025](https://a2e.ai/best-self-hosted-tts-models-2025/)
- [Piper TTS](https://github.com/rhasspy/piper) — Fast local neural TTS

---

*This document complements the speech recognition research at `tho-speech-recognition.md`. Together they cover the full voice I/O pipeline for DAEMON.*
