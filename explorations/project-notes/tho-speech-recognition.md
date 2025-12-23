# Speech Recognition Options for Tho

Research notes for implementing speech-to-text in Tho.

---

## Current State

Tho's architecture doc (`docs/architecture.md`) mentions four STT options:
1. Wispr Flow (external, Kenny already uses)
2. OpenAI Whisper API (cloud)
3. Local Whisper (whisper.cpp)
4. Web Speech API (browser built-in)

The current recommendation is to leverage Wispr Flow. This research explores what in-app STT would look like if/when it becomes desirable.

---

## Option 1: Keep Using External STT (Wispr Flow)

**What it is:** System-level dictation tool that works in any app.

**Pros:**
- Already working, zero development effort
- High quality (uses cloud AI)
- Works everywhere, not just in Tho
- Features: auto-formatting, tone matching, error correction

**Cons:**
- $12/month subscription
- Cloud-based (privacy concerns)
- No programmatic control from Tho
- Can't trigger recording from within the app
- Can't access transcription events for app-specific features

**Verdict:** Good for now, but limits what Tho can do with voice.

---

## Option 2: Transformers.js + Whisper (Browser/WebGPU)

**What it is:** Run OpenAI's Whisper model directly in Electron's renderer process using `@huggingface/transformers` (formerly `@xenova/transformers`).

**How it works:**
```javascript
import { pipeline } from '@huggingface/transformers';

const transcriber = await pipeline(
  'automatic-speech-recognition',
  'Xenova/whisper-small',
  { device: 'webgpu' }  // or 'wasm' for CPU fallback
);

const result = await transcriber(audioBlob);
console.log(result.text);
```

**Performance (from GitHub issues and demos):**
- Mac M2 with WASM: ~1 second for short phrases
- WebGPU can be faster, but on some Macs WASM beats WebGPU (surprising)
- First load downloads model (base ~73MB, cached after)
- Distil-Whisper: 49% smaller, 4.2x faster than standard Whisper

**Models available:**
- `whisper-tiny` (~40MB) - fastest, lowest quality
- `whisper-base` (~73MB) - good balance
- `whisper-small` (~240MB) - better quality
- `distil-whisper-small.en` - optimized, English-only

**Pros:**
- Fully local/offline after model download
- No API costs
- Works in Electron renderer
- Good ecosystem (HuggingFace)
- Supports 100+ languages
- WebGPU acceleration available

**Cons:**
- Initial model download
- Uses browser memory/resources
- Quantization-sensitive (quality varies with settings)
- WebGPU support ~70% globally (fine for Tho's macOS target)

**Electron-specific:**
- There's a fork: [transformersjs-electron](https://github.com/Mintplex-Labs/transformersjs-electron) for bundled apps
- Standard package works but may need config tweaks

**Demo:** [whisper-web](https://github.com/xenova/whisper-web)

---

## Option 3: whisper-node (Native Bindings)

**What it is:** Node.js bindings for whisper.cpp (C++ Whisper port).

**Installation:**
```bash
npm install whisper-node
npx whisper-node download  # downloads model
```

**Usage:**
```javascript
import whisper from 'whisper-node';

const transcript = await whisper('audio.wav', {
  modelName: 'base.en',
  whisperOptions: {
    language: 'auto',
    word_timestamps: true
  }
});
// Returns: [{ start, end, speech }]
```

**Pros:**
- Native performance (faster than WASM for long audio)
- Word-level timestamps
- Proven library (used in production)

**Cons:**
- Native dependencies (needs build tools on dev machine)
- Electron native module complexities (rebuild for Electron)
- File-based input (need to write audio to temp file)
- Less convenient than pure JS solution

**Alternative:** `nodejs-whisper` - similar approach, auto-converts audio formats.

---

## Option 4: macOS Native (SFSpeechRecognizer)

**What it is:** Apple's built-in speech recognition framework.

**Features:**
- On-device recognition available (iOS A9+, all Macs)
- No network required when using `requiresOnDeviceRecognition`
- 10+ languages supported offline
- Rate-limited for server-based: 1000 req/hour, 1 min/request

**Integration approaches:**
1. Swift companion tool called from Electron via child_process
2. Native Electron module (complex)

**CLI tool exists:** There's a macOS CLI that uses SFSpeechRecognizer to transcribe microphone input.

**Pros:**
- No model download (OS-provided)
- Fast startup
- System-level integration
- Free, no API costs

**Cons:**
- macOS only (not cross-platform)
- Less accurate than cloud or Whisper
- Requires Swift/native code
- Privacy permissions needed

---

## Option 5: Standalone macOS Apps (VoiceInk, SuperWhisper)

**What they are:** Native macOS apps running Whisper locally.

**VoiceInk:**
- Open source
- $19-29 one-time
- Fully offline

**SuperWhisper:**
- Privacy-focused
- Offline-first
- One-time purchase

**Integration with Tho:**
These are standalone apps, not libraries. But worth knowing as alternatives to Wispr Flow if privacy is a concern.

---

## Recommendation for Tho

### Short Term: Keep Wispr Flow
No development needed. Kenny already has it. Works well.

### Medium Term: Add Optional In-App STT

If we want in-app voice control (push-to-talk button, voice commands, etc.):

**Recommended approach: Transformers.js + Whisper**

Rationale:
1. **Pure JavaScript** - no native module headaches
2. **Electron-friendly** - runs in renderer process
3. **Offline** - privacy, no ongoing costs
4. **Good quality** - Whisper is state-of-the-art
5. **Active ecosystem** - HuggingFace maintains it

**Implementation sketch:**

1. Add recording button to InputArea (alongside camera)
2. Capture audio via MediaRecorder API
3. On stop, send audio blob to Whisper pipeline
4. Insert transcription into input field
5. User can edit/send

```typescript
// Rough implementation idea
import { pipeline } from '@huggingface/transformers';

let transcriber: any = null;

async function initSTT() {
  transcriber = await pipeline(
    'automatic-speech-recognition',
    'Xenova/whisper-base',
    { device: navigator.gpu ? 'webgpu' : 'wasm' }
  );
}

async function transcribe(audioBlob: Blob): Promise<string> {
  const result = await transcriber(audioBlob);
  return result.text;
}
```

**Model choice:**
- Start with `whisper-base` (~73MB)
- Consider `distil-whisper-small.en` if English-only is acceptable (faster)

**UX considerations:**
- Show model download progress on first use
- Indicate when transcription is processing
- Allow fallback to typing if STT fails
- Consider voice activity detection for automatic segmentation

---

## Questions for Kenny

1. Is in-app STT actually needed, or is Wispr Flow sufficient?
2. English-only acceptable, or need multilingual?
3. Push-to-talk, or voice activity detection?
4. Okay with ~73MB model download on first use?

---

## References

- [Transformers.js Documentation](https://huggingface.co/docs/transformers.js/en/index)
- [whisper-web demo](https://github.com/xenova/whisper-web)
- [transformersjs-electron fork](https://github.com/Mintplex-Labs/transformersjs-electron)
- [whisper-node npm](https://www.npmjs.com/package/whisper-node)
- [SFSpeechRecognizer Apple Docs](https://developer.apple.com/documentation/speech/sfspeechrecognizer)
- [Picovoice (wake word + local STT)](https://medium.com/picovoice/its-time-for-local-speech-recognition-df7c911fe944)
- [VoiceInk vs Wispr Flow](https://tryvoiceink.com/wispr-flow-alternative)

---

*Research completed: 2025-12-23, Session 9*
