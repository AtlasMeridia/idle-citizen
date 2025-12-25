# DAEMON Interface Implementation Guide

**Created:** 2024-12-24
**Purpose:** Define the interaction layer for DAEMON — voice, avatar, and system presence
**Complements:** Orchestrator guide, TTS/STT research, personality configuration

---

## Overview

This guide covers the **user-facing layer** of DAEMON — how the human interacts with their AI companion. The orchestrator handles intelligence; this layer handles presence.

The goal: DAEMON should feel like a persistent presence, not an app you launch.

---

## 1. Recommended Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     SYSTEM TRAY                              │
│  (Always visible, minimal resources, click to expand)        │
└──────────────────────────┬──────────────────────────────────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
     ┌──────────┐    ┌──────────┐    ┌──────────┐
     │  Quick   │    │   Main   │    │  Voice   │
     │  Menu    │    │  Window  │    │  Mode    │
     │          │    │          │    │          │
     │ Commands │    │ Chat +   │    │ Listen + │
     │ Status   │    │ Avatar   │    │ Respond  │
     └──────────┘    └──────────┘    └──────────┘
           │               │               │
           └───────────────┼───────────────┘
                           │
                           ▼
                  ┌────────────────┐
                  │ Tauri Backend  │
                  │    (Rust)      │
                  └────────┬───────┘
                           │
                           ▼
                  ┌────────────────┐
                  │  Orchestrator  │
                  │   (Python)     │
                  └────────────────┘
```

---

## 2. Framework Choice: Tauri 2.0

**Recommendation: Tauri over Electron**

| Factor | Tauri | Electron |
|--------|-------|----------|
| Binary size | 2.5-3 MB | 150+ MB |
| Memory (idle) | 30-40 MB | 200-300 MB |
| System tray | Native | Emulated |
| Apple Silicon | Excellent | Good |
| Security model | Built-in | Manual |

Tauri 2.0 (released 2024) specifically added:
- Multi-window support
- System tray improvements
- Mobile support (future-proofing)
- Permission model by default

**Why This Matters for DAEMON:**
- Always-on presence requires low resource consumption
- System tray is native, not a workaround
- Rust backend pairs well with Python orchestrator (FFI or IPC)
- No Chromium tax for background voice processing

---

## 3. Interface Modes

DAEMON should support three interaction modes:

### Mode 1: Ambient (Default)

- System tray icon only
- Listening for wake word (optional)
- Minimal resource usage
- Click tray → Quick menu or Main window

**Implementation:**
```rust
// Tauri system tray setup
let tray = TrayIconBuilder::new()
    .icon(icon)
    .menu(&quick_menu)
    .on_tray_icon_event(|tray, event| {
        match event.click_type {
            ClickType::Left => toggle_main_window(),
            ClickType::Right => show_quick_menu(),
            _ => {}
        }
    })
    .build(app)?;
```

### Mode 2: Conversational (Main Window)

- Chat interface with message history
- Optional avatar display
- Voice input/output available
- Full memory context visible

**Window Layout:**
```
┌─────────────────────────────────────┐
│  ┌─────────────┐  ┌──────────────┐  │
│  │             │  │   Messages   │  │
│  │   Avatar    │  │              │  │
│  │             │  │   [Claude]   │  │
│  │  (Live2D)   │  │   [User]     │  │
│  │             │  │   [Claude]   │  │
│  └─────────────┘  │              │  │
│                   │   ...        │  │
│  ┌─────────────┐  │              │  │
│  │   Memory    │  ├──────────────┤  │
│  │   Context   │  │  [Input   ]  │  │
│  │   (fade)    │  │  🎤 Send     │  │
│  └─────────────┘  └──────────────┘  │
└─────────────────────────────────────┘
```

### Mode 3: Voice-Only

- No visible window (or minimal overlay)
- Push-to-talk or wake-word activated
- DAEMON responds via TTS
- Good for hands-free workflows

**Activation Options:**
- Global hotkey (e.g., double-tap Cmd)
- Wake word ("Hey DAEMON")
- Tray menu → "Voice Mode"

---

## 4. Voice Pipeline

### Speech-to-Text (STT)

**Recommended: Faster-Whisper**
- 4-15x faster than vanilla Whisper
- Uses CTranslate2 for optimized inference
- Supports Apple Silicon (CPU mode efficient)

**Real-time Pipeline:**
```
Microphone
    ↓
WebRTC VAD (voice activity detection)
    ↓ (voice detected)
Faster-Whisper (streaming mode)
    ↓
Text → Orchestrator
```

**Libraries:**
- `faster-whisper`: Core transcription
- `SileroVAD`: Voice activity detection (16ms latency)
- `PyAudio` or `sounddevice`: Audio capture

**Configuration:**
```python
from faster_whisper import WhisperModel

model = WhisperModel("small", device="cpu", compute_type="int8")
# small = good balance of speed/accuracy
# int8 = efficient on Apple Silicon
```

### Text-to-Speech (TTS)

**Recommended: Kokoro TTS**
- 82M parameters (lightweight)
- 54 voices across 8 languages
- Runs 3-11x real-time on CPU
- Apache 2.0 licensed

**Integration:**
```python
from kokoro import KokoroTTS

tts = KokoroTTS()
audio = tts.generate("Hello, I'm DAEMON.", voice="af_bella")
# Returns audio array, play via sounddevice
```

**Voice Selection:**
- Store preferred voice in personality config
- Allow voice switching via command
- Consider: cloned voice using RVC (advanced)

### Wake Word Detection

**Option A: SileroVAD + Keyword**
- VAD detects speech
- First 1-2 seconds → check for wake word
- If match → continue transcription

**Option B: Porcupine**
- Commercial but has free tier
- Highly optimized wake word detection
- Custom wake words require training

**Recommendation:** Start with hotkey, add wake word later.

---

## 5. Avatar System

### Phase 1: Static Avatar

For initial implementation:
- Single character image
- 3-4 states: idle, listening, thinking, speaking
- CSS transitions between states

**Implementation:**
```html
<div class="avatar" data-state="idle">
  <img src="daemon-idle.png" class="state-idle" />
  <img src="daemon-listening.png" class="state-listening" />
  <img src="daemon-thinking.png" class="state-thinking" />
  <img src="daemon-speaking.png" class="state-speaking" />
</div>
```

### Phase 2: Live2D Integration

For richer visual presence:

**Tools:**
- **Live2D Cubism Editor**: Create/rig character
- **Live2D Cubism SDK**: Runtime animation
- **pixi-live2d-display**: Web-compatible renderer

**Expression Control:**
```javascript
// pixi-live2d-display integration
const model = await PIXI.live2d.Live2DModel.from("daemon.model3.json");

// Emotion-based expression
model.expression("happy");

// Lip sync from audio
model.speak(audioUrl, { volume: 0.5 });
```

**Reference Project: Open-LLM-VTuber**
- Complete Live2D + LLM integration
- 7+ ASR providers, 18+ TTS providers
- Good architecture reference

### Avatar Source Options

1. **Midjourney/DALL-E generated**
   - Quick to create
   - May lack consistency across expressions

2. **Custom commissioned**
   - Higher quality
   - Full control over expressions

3. **VRoid Studio**
   - Free 3D character creator
   - Export to Live2D compatible format

4. **Existing Live2D models**
   - BOOTH marketplace
   - Open-source models

---

## 6. System Tray Integration

### Quick Menu Structure

```
DAEMON ▾
├── 💬 Open Chat
├── 🎤 Voice Mode
├── ─────────────
├── 📊 Memory Stats
│   └── "1,247 memories | 34 sessions"
├── ⚙️ Settings
├── ─────────────
├── 🔄 Switch Model
│   ├── ○ Qwen 2.5 72B
│   ├── ● Qwen 2.5 7B (active)
│   └── ○ DeepSeek R1 32B
├── ─────────────
└── ⏻ Quit DAEMON
```

### Status Indicators

Tray icon should indicate state:
- **Green dot**: Active, listening
- **Yellow dot**: Processing
- **Gray**: Ambient (not listening)
- **Red**: Error state

### Hotkeys

Recommend registering global hotkeys:
- `Cmd+Shift+D`: Open/focus main window
- `Cmd+Shift+V`: Toggle voice mode
- `Escape`: Hide window (not quit)

---

## 7. Frontend Stack

**Recommended:**
```
Tauri 2.0
├── Frontend: React or Svelte
├── Styling: Tailwind CSS
├── State: Zustand or Jotai
├── IPC: Tauri commands (typed)
└── Avatar: pixi-live2d-display
```

**Why React/Svelte over vanilla:**
- Component-based avatar + chat
- State management for conversation
- Easy to iterate on UI

**Why Tailwind:**
- Consistent with headless-atlas design system
- Dark theme by default
- Rapid prototyping

---

## 8. Tauri ↔ Python Communication

The Tauri (Rust) frontend needs to communicate with the Python orchestrator.

### Option A: HTTP/WebSocket (Recommended)

```
Tauri Frontend
      ↓ (HTTP/WS)
Python Orchestrator (FastAPI)
      ↓
Ollama + Mem0 + Tools
```

**Implementation:**
- Python runs FastAPI server on localhost:8000
- Tauri makes HTTP requests or opens WebSocket
- WebSocket for streaming responses

```python
# Python side (FastAPI)
from fastapi import FastAPI, WebSocket

app = FastAPI()

@app.websocket("/chat")
async def chat(websocket: WebSocket):
    await websocket.accept()
    while True:
        message = await websocket.receive_text()
        async for chunk in orchestrator.stream_response(message):
            await websocket.send_text(chunk)
```

```typescript
// Tauri side
const ws = new WebSocket("ws://localhost:8000/chat");
ws.onmessage = (event) => {
  appendToChat(event.data);
};
```

### Option B: PyO3 (Advanced)

- Embed Python in Rust via PyO3
- Lower latency, tighter integration
- More complex setup
- Better for production

### Option C: Subprocess + Stdio

- Launch Python as subprocess
- Communicate via stdin/stdout JSON
- Simple but harder to debug

**Recommendation:** Start with HTTP/WebSocket for development flexibility.

---

## 9. Directory Structure

```
daemon-interface/
├── src-tauri/
│   ├── src/
│   │   ├── main.rs          # Tauri entry
│   │   ├── tray.rs          # System tray logic
│   │   └── commands.rs      # IPC commands
│   ├── icons/               # App + tray icons
│   └── tauri.conf.json      # Tauri config
├── src/
│   ├── App.tsx              # Main React app
│   ├── components/
│   │   ├── Avatar.tsx       # Live2D/static avatar
│   │   ├── Chat.tsx         # Message history
│   │   ├── Input.tsx        # Text + voice input
│   │   └── MemoryPanel.tsx  # Memory context display
│   ├── hooks/
│   │   ├── useVoice.ts      # Voice input hook
│   │   └── useWebSocket.ts  # Orchestrator connection
│   └── styles/
│       └── globals.css      # Tailwind + custom
├── public/
│   ├── avatar/              # Avatar assets
│   └── sounds/              # UI sounds
└── package.json
```

---

## 10. Implementation Phases

### Phase 1: Minimal Viable Interface

**Goal:** Text chat with system tray, no voice or avatar.

1. Create Tauri project with React
2. Implement system tray with quick menu
3. Build basic chat UI
4. Connect to orchestrator via WebSocket
5. Add memory context panel

**Deliverables:**
- Runnable app with tray icon
- Chat works end-to-end
- Can minimize to tray

### Phase 2: Voice Integration

**Goal:** Add voice input/output.

1. Integrate Faster-Whisper for STT
2. Integrate Kokoro for TTS
3. Add voice mode toggle
4. Implement push-to-talk
5. Add voice indicators in UI

**Deliverables:**
- Can speak to DAEMON
- DAEMON responds with voice
- Visual feedback for listening state

### Phase 3: Avatar

**Goal:** Visual presence.

1. Create or acquire avatar assets
2. Integrate static avatar with states
3. Sync avatar state with conversation
4. (Optional) Live2D integration

**Deliverables:**
- Avatar visible in main window
- Expressions match conversation
- (Advanced) Lip sync with TTS

### Phase 4: Polish

**Goal:** Refined experience.

1. Global hotkeys
2. Animation polish
3. Notification support
4. Error handling UI
5. Settings panel

---

## 11. Design Principles

### 1. Presence Over Features

DAEMON should feel present even when minimized. The tray icon, ambient listening, and quick responses create a sense of availability.

### 2. Graceful Degradation

- No voice? Text works.
- No avatar? Chat works.
- No internet? Local models work.
- Model slow? Show thinking state.

### 3. Respect Attention

- No unsolicited notifications
- No auto-play sounds
- DAEMON waits to be addressed
- Easy to dismiss/minimize

### 4. Personality Through UI

The interface should reflect DAEMON's personality:
- Color palette matches configured mood
- Animation speed matches configured tempo
- Voice tone matches configured personality

---

## 12. Reference Projects

**Open-LLM-VTuber**
- https://github.com/Open-LLM-VTuber/Open-LLM-VTuber
- Complete voice + Live2D + LLM integration
- Multi-modal input support
- Good architecture reference

**Jan AI**
- https://jan.ai
- Open-source ChatGPT alternative
- Clean Electron UI (reference for chat design)
- MCP integration

**Tauri + React Template**
- https://github.com/tauri-apps/create-tauri-app
- Official starter with React
- System tray example included

---

## 13. Next Steps

1. **Set up Tauri project** with React frontend
2. **Create basic chat UI** connected to orchestrator
3. **Implement system tray** with quick menu
4. **Add voice pipeline** (Faster-Whisper + Kokoro)
5. **Integrate static avatar** with expression states
6. **Iterate on UX** based on usage

The interface is where DAEMON becomes real. The orchestrator is the brain; this is the face.

---

*This guide complements the orchestrator implementation guide. Together they define DAEMON's complete architecture.*
