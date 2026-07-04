<p align="center">
  <img src="https://img.shields.io/badge/PROJECT-ULTRON-red?style=for-the-badge&logo=probot&logoColor=white" />
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white" />
  <img src="https://img.shields.io/badge/AI-Groq%20LPU-green?style=for-the-badge" />
</p>

<h1 align="center">🤖 PROJECT ULTRON</h1>
<h3 align="center">Autonomous Agentic AI — Chief of Staff — Super OS</h3>

<p align="center">
  <em>The most feature-rich single-developer AI desktop assistant in existence.</em><br/>
  <em>Computer Vision + Voice + LLM + Desktop Automation + Quantum Randomness — all in one system.</em>
</p>

---

## 🧠 What is Ultron?

Ultron is a **fully autonomous AI assistant** built for Windows that combines:

- **Natural Language Intelligence** (Groq LPU + Llama) for lightning-fast AI reasoning
- **Computer Vision** (MediaPipe) for hand gesture control, eye-gaze tracking, and face recognition
- **Neural Voice** (Edge-TTS + Vosk) with emotion-modulated speech and wake-word detection
- **System Automation** that can open apps, run commands, search the web, send emails, and manage files
- **Photographic Memory** (ChromaDB + EasyOCR) that remembers everything you've ever shown it
- **Quantum Randomness** (IBM Qiskit) for true randomness from actual quantum processors

> Built by **Surya Ramisetty** — one developer, zero limits.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                    ULTRON CORE                       │
│              (ultron.py — Agentic Brain)             │
├─────────────┬───────────────┬───────────────────────┤
│  VOICE      │  VISION       │  AUTOMATION           │
│  ─────      │  ──────       │  ──────────           │
│  Vosk Wake  │  Hand Gesture │  System Control       │
│  Edge-TTS   │  Eye Gaze     │  Web Search           │
│  Whisper    │  Face Recog   │  App Launcher         │
│  VAD        │  Air Volume   │  File Manager         │
│  Emotion    │  Swipe Nav    │  Email Agent          │
├─────────────┼───────────────┼───────────────────────┤
│  MEMORY     │  SECURITY     │  PRODUCTIVITY         │
│  ──────     │  ────────     │  ────────────         │
│  ChromaDB   │  Biometric    │  Ghostwriter          │
│  Rewind     │  Quantum      │  Voice Dictation      │
│  Semantic   │  Encryption   │  PDF Summarizer       │
│  OCR Cache  │  Focus Guard  │  Clipboard Butler     │
├─────────────┴───────────────┴───────────────────────┤
│               COMMUNICATION LAYER                    │
│  Mobile Uplink │ WhatsApp Bot │ Email Agent │ HUD UI │
└─────────────────────────────────────────────────────┘
```

---

## ⚡ Features (28 Phases of Evolution)

### 🎤 Voice & Audio (Phase 28 — Latest)
| Feature | Description |
|---------|-------------|
| **Wake-Word Detection** | Say "Ultron" to activate — always listening via Vosk |
| **Neural Voice (Edge-TTS)** | Human-like speech with Christopher Neural voice |
| **Emotion Modulation** | Adjusts pitch/rate based on context (happy, sad, angry, excited) |
| **Voice Interruption** | Say "Stop" mid-sentence — Silero VAD detects speech instantly |
| **Voice Macros** | Spoken phrases trigger custom scripts/commands |
| **Noise Adapter** | Auto-raises volume when ambient noise increases |
| **Voice Dictation** | Real-time speech-to-text for any application |

### 👁️ Computer Vision (Phase 24)
| Feature | Description |
|---------|-------------|
| **Hand Gesture Mouse** | Control cursor with index finger via MediaPipe |
| **Air-Click** | Pinch thumb + index to click, middle for right-click |
| **Air Volume Dial** | Second hand controls system volume |
| **Swipe Navigation** | Fast wrist swipe = switch desktops |
| **Eye-Gaze Scrolling** | Look up/down to scroll pages |
| **Face Recognition** | Biometric authentication via face mesh |

### 🧠 Intelligence
| Feature | Description |
|---------|-------------|
| **Groq LPU Brain** | Llama 3 via Groq API — sub-second response times |
| **Agentic Tool Use** | 15+ tools called autonomously (search, email, code, apps) |
| **Semantic Memory** | ChromaDB stores all conversations for future recall |
| **Photographic Rewind** | EasyOCR captures screen text every 30s for total recall |
| **Time-Aware Personality** | Adjusts tone based on time of day |
| **Fun Mode** | Toggle sarcastic, unhinged personality |

### 🔧 Automation & Productivity
| Feature | Description |
|---------|-------------|
| **System Control** | Open/close apps, adjust brightness/volume, lock screen |
| **Web Search** | DuckDuckGo integration for live information |
| **Email Agent** | Read, compose, and send emails via Gmail API |
| **Ghostwriter** | PyQt6 overlay for AI autocomplete in any text field |
| **PDF Summarizer** | Drag-and-drop PDF → instant extractive summary |
| **Clipboard Butler** | Auto-extracts emails & URLs from clipboard |
| **Workspace Spawner** | One command opens all your project folders, files, and URLs |
| **Site Blocker** | Block distracting sites during focus sessions |
| **Auto-Coder** | Scan, execute, debug, and fix Python projects autonomously |

### 🔐 Security
| Feature | Description |
|---------|-------------|
| **Quantum Cryptography** | IBM Qiskit quantum-generated encryption keys |
| **Focus Guard** | Monitors work sessions and blocks distractions |
| **Biometric Engine** | Face-based authentication |

### 📱 Communication
| Feature | Description |
|---------|-------------|
| **Mobile Uplink** | Control Ultron from your phone |
| **WhatsApp Bot** | Selenium-based WhatsApp automation |
| **HUD Overlay** | Transparent always-on-top status display |

---

## 📁 Project Structure

```
BUUDY_AI/
├── ultron.py                  # Main entry point — Agentic Brain
├── buddy_ai/
│   ├── ultron_vision.py       # Computer vision (hand/eye/face)
│   ├── ultron_memory.py       # ChromaDB semantic memory
│   ├── ultron_mobile.py       # Mobile uplink
│   ├── ultron_hud.py          # HUD overlay UI
│   ├── agent_manager.py       # Multi-agent orchestration
│   ├── base_agent.py          # Agent base classes & event bus
│   ├── command_normalizer.py  # NLP command normalization
│   ├── liquid_ui.py           # Liquid morphing UI
│   └── skills/
│       ├── voice_interruption.py   # VAD-based speech stop
│       ├── emotion_modulation.py   # Emotion-aware TTS
│       ├── voice_macros.py         # Spoken phrase triggers
│       ├── noise_adapter.py        # Ambient noise volume adjust
│       ├── site_blocker.py         # Focus-mode site blocking
│       ├── clipboard_butler.py     # Clipboard email/URL extract
│       ├── pdf_summarizer.py       # Offline PDF summarization
│       ├── workspace_spawner.py    # Multi-item workspace launcher
│       ├── ghostwriter.py          # AI autocomplete overlay
│       ├── voice_dictation.py      # Real-time speech-to-text
│       ├── wake_word.py            # Vosk wake-word engine
│       ├── rewind_engine.py        # Photographic memory
│       ├── quantum_engine.py       # IBM Qiskit integration
│       ├── quantum_cryptography.py # Quantum encryption
│       ├── system_control.py       # OS automation
│       ├── search.py               # Web search
│       ├── phone_bridge.py         # Mobile bridge
│       ├── ai_swarm.py             # Multi-agent swarm
│       ├── auto_coder.py           # Autonomous code debugger
│       ├── biometric_engine.py     # Face authentication
│       ├── focus_guard.py          # Distraction blocker
│       └── ... (40+ skill modules)
├── config/
│   └── voice_features.yaml    # Feature toggles & settings
├── core/
│   ├── agent_registry.py      # Agent registration
│   ├── base_agent.py          # Abstract agent class
│   ├── command_queue.py       # Command queue
│   ├── error_handler.py       # Error handling
│   ├── event_bus.py           # Pub/sub event system
│   └── intent_router.py       # Regex intent router
├── dashboard/                 # Web dashboard
├── model/                     # Vosk speech model
└── .env                       # API keys (not committed)
```

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.10+**
- **Windows 10/11**
- **Vosk Model** — download `vosk-model-small-en-us-0.15` to `model/` directory
- **Groq API Key** — get one at [console.groq.com](https://console.groq.com)

### Installation

```bash
# Clone the repository
git clone https://github.com/suryaramisetty70-pyt/ultron.git
cd ultron

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r buddy_ai/requirements.txt

# Set up environment variables
# Create .env file with:
# GROQ_API_KEY=your_key_here
# IBM_QUANTUM_KEY=your_key_here (optional)
# GMAIL_APP_PASSWORD=your_password_here (optional)

# Download Vosk model
python download_model.py

# Launch Ultron
python ultron.py
```

### Voice Commands
```
"Ultron"              → Wake up
"Stop"                → Interrupt speech
"Open [app name]"     → Launch application
"Search for [query]"  → Web search
"Send email to ..."   → Compose & send email
"Fun mode"            → Toggle sarcastic personality
"Exit" / "Quit"       → Shutdown
```

---

## 🏆 Competitive Position

| vs. Competitor | Stars | Voice | Vision | LLM | Desktop Auto | Unique Edge |
|---|---|---|---|---|---|---|
| **Ultron** | — | ✅ Full | ✅ Full | ✅ Groq | ✅ Full | CV + Quantum + Emotion TTS + Ghostwriter |
| Open Interpreter | 64k | ❌ | ❌ | ✅ Multi | ✅ Code | Multi-language code exec |
| Leon AI | 17k | ✅ Basic | ❌ | ✅ | ✅ Skills | Web UI, community |
| Pipecat | 13k | ✅ Pro | ⚠️ | ✅ Multi | ❌ | Ultra-low latency voice |
| PyGPT | 1.8k | ✅ | ✅ Camera | ✅ Multi | ✅ | Multi-model, desktop UI |
| Mycroft (archived) | 6.6k | ✅ | ❌ | ❌ | ✅ | Smart home integration |

**Ultron's moat**: No other project combines computer vision + voice + LLM + quantum randomness + desktop automation in a single package.

---

## 📋 Roadmap

- [x] Phase 1-23: Core AI, voice, system control, email, web search
- [x] Phase 24: Computer vision (hand gesture, eye gaze, face recognition)
- [x] Phase 25: Quantum engine, security, biometrics
- [x] Phase 26: Photographic rewind memory, mobile uplink
- [x] Phase 27: Ghostwriter overlay, voice dictation, wake-word engine
- [x] Phase 28: Voice & audio suite (emotion TTS, macros, noise adapter, PDF summarizer, clipboard butler, workspace spawner, site blocker)
- [ ] Phase 29: Multi-LLM support (OpenAI, Anthropic, Ollama local)
- [ ] Phase 30: Home automation (Home Assistant integration)
- [ ] Phase 31: Docker containerization & CI/CD pipeline

---

## 🛡️ Security Notes

- API keys should be stored in `.env` (never committed to source)
- The site blocker requires Administrator privileges to edit the hosts file
- Face recognition data is stored locally only
- Quantum keys are generated from IBM quantum processors

---

## 📜 License

This project is proprietary software created by **Surya Ramisetty**.

---

<p align="center">
  <strong>🔴 PROJECT ULTRON — One developer. Zero limits. Infinite capability. 🔴</strong>
</p>
