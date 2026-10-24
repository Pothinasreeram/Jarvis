# J.A.R.V.I.S. (Just A Rather Very Intelligent System)
### *Next-Generation Autonomous Desktop AI Assistant & Sci-Fi Neural Interface*

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Local AI](https://img.shields.io/badge/Ollama-LLaMA_3.1:8B_%7C_Gemma_3-000000?style=for-the-badge&logo=ollama&logoColor=white)](https://ollama.ai/)
[![GUI](https://img.shields.io/badge/CustomTkinter-Modular_Panels-00b4d8?style=for-the-badge)](https://github.com/TomSchimansky/CustomTkinter)
[![Tests](https://img.shields.io/badge/Tests-29%20Passed%20%E2%9C%94-00ff66?style=for-the-badge)](tests/)
[![Platform](https://img.shields.io/badge/Platform-Windows_10_%2F_11-0078D6?style=for-the-badge&logo=windows&logoColor=white)](https://www.microsoft.com/)

---

## 🌌 Overview

**J.A.R.V.I.S.** is an open-source, locally hosted autonomous AI desktop assistant inspired by Tony Stark's iconic system. Engineered with a **modular 42-skill architecture**, J.A.R.V.I.S. integrates **local Large Language Models (LLaMA 3.1:8b)**, **MediaPipe neural hand tracking with live holographic viewfinder**, **Windows PSAPI memory optimization**, **acoustic speaker biometrics**, **computer vision desk security**, and a **hardware-accelerated sci-fi HUD** with decoupled panel components.

Operating entirely offline for core tasks with zero cloud subscription lock-in, J.A.R.V.I.S. manages technical research synthesis, hardware thermal diagnostics, voice-authenticated workstation locks, media control, multi-command action chaining, and daily executive morning briefings.

---

## 🏛️ System Architecture

```mermaid
graph TD
    User([🎤 User Voice / ⌨️ HUD Console / 🖐️ Hand Gestures / 🖱️ Tray / Hotkey: Ctrl+Space]) --> AudioPipeline[Voice & Input Pipeline]
    
    subgraph AudioPipeline [Audio & Input Pipeline]
        OWW[OpenWakeWord ONNX Engine] --> |'Hey Jarvis'| STT[Speech-to-Text Transcriber]
        VP[Voiceprint Biometrics: MFCC + Cosine Sim] --> |Speaker Match| Gatekeeper{Security Check}
        Gestures[MediaPipe Vision: 21 Neon Hand Landmarks] --> |Air Gestures| GestureRouter[Gesture Command Engine]
    end

    Gatekeeper --> |Authenticated| CoreRouter[Central Skill Manager & Multi-Action Router]
    GestureRouter --> CoreRouter

    subgraph IntelligenceCore [Intelligence & Neural Core]
        LLM[Ollama: LLaMA 3.1:8b Local]
        VisionLLM[Ollama: Gemma 3 Vision]
        Memory[SQLite + JSON Vector Context]
    end

    CoreRouter --> IntelligenceCore
    CoreRouter --> ExecutiveSkills[42 Modular Voice Skills]

    subgraph ExecutiveSkills [Executive Skill Layers]
        Sentry[👁️ Desk Sentry: Haar Cascade Auto-Lock]
        Research[🧠 Autonomous Deep Research Agent]
        Taskmaster[📋 Stark Taskmaster: SQLite Directives]
        Diagnostics[⚡ Mark VII Hardware Diagnostics]
        Briefing[🌅 Executive Morning Briefing]
        WebNav[🌐 Stark Web Navigator & Hacker News]
        Protocols[🎛️ Protocols: Work, Gaming, Stealth]
        AutoPilot[🤖 Desktop Auto-Pilot & OS Control]
        Wellness[🧘 Wellness & Ergonomics Coach]
        Maid[🧹 Maid Protocol: Deduplicator & Cleaner]
        CodingCopilot[💻 Developer Copilot: LLaMA Code Gen]
    end

    ExecutiveSkills --> FeedbackLoop[HUD Telemetry & Audio Dispatch]
    
    subgraph FeedbackLoop [Modular HUD Panels & Output Interface]
        HUD[Modular CustomTkinter Dashboard in gui/panels/]
        ArcReactor[Dynamic Audio-Reactive Arc Reactor & FFT Equalizer]
        PiperTTS[Offline Piper TTS: Paul Bettany Clone / Edge-TTS]
        SoundFX[Synthesized Iron Man WAV Sound FX]
        Tray[Windows System Tray Hub]
    end
```

---

## 📊 Implementation Status & Verification Matrix

To provide full transparency, features are categorized by current verification status:

| Subsystem | Feature | Status | Notes |
| :--- | :--- | :---: | :--- |
| **HUD & GUI** | Modular Panels (`gui/panels/`) | `✔ Stable` | Decoupled telemetry, reactor, media, directives, environment, and controls. |
| **HUD & GUI** | Dynamic Arc Reactor & 36-Band FFT Equalizer | `✔ Stable` | Real-time Tkinter canvas animations with mic reactivity. |
| **HUD & GUI** | Anchored Viewport Terminal & Command Input | `✔ Stable` | Permanently pinned bottom console & dock with zero display clipping. |
| **HUD & GUI** | Global Hotkey (`Ctrl + Space`) & System Tray | `✔ Stable` | Instant summon/minimize via Windows API `RegisterHotKey`. |
| **Memory Opt** | Windows PSAPI One-Click RAM Purge | `✔ Stable` | `EmptyWorkingSet()` trims working sets across active processes, reclaiming up to 1.8GB+. |
| **Computer Vision**| Hand Gesture Control (`gesture_skill.py`) | `✔ Stable` | MediaPipe neural hand tracking: air volume pinch, speech interrupts, briefings. |
| **Computer Vision**| Live Holographic Viewfinder Window | `✔ Stable` | OpenCV HUD popup rendering 21 neon cyan landmarks, bone connectors, and confidence. |
| **Skill Router** | 42 Modular Skills Engine | `✔ Stable` | Priority-based routing, dynamic loading, and 100% test-verified dispatch. |
| **Command Engine**| Multi-Command Action Chaining | `✔ Stable` | Intelligent conjunction splitting and verb inheritance (`open chrome and notepad`). |
| **Architecture** | Graceful Lifecycle & Structured Logging | `✔ Stable` | Controlled startup/shutdown releasing webcam & audio, with unified file logger. |
| **Environment** | Resilient Weather Controller | `✔ Stable` | Tomorrow.io $\rightarrow$ zero-key Open-Meteo fallback $\rightarrow$ cache. |
| **Task Directives**| Stark Taskmaster | `✔ Stable` | SQLite-backed directive checklist with interactive `✔` buttons. |
| **Developer Tools**| Coding Copilot (`coding_skill.py`) | `✔ Stable` | Synthesizes Python scripts and writes them to the Desktop. |
| **Local AI** | LLaMA 3.1:8b Local Chat & Reasoning | `⚡ Local Setup` | Requires local Ollama instance (`ollama pull llama3.1:8b`). |
| **Computer Vision**| Gemma 3 Screen Analysis & Webcam Inspection | `⚡ Local Setup` | Requires Ollama vision model + local webcam device. |
| **Biometrics** | Voiceprint Speaker Authentication | `⚡ Experimental` | MFCC acoustic extraction; calibrates to individual speaker timber. |
| **Desk Sentinel** | Webcam Sentry Auto-Lock | `⚡ Experimental` | OpenCV Haar Cascade presence detector auto-locks Windows when away. |
| **Voice Engine** | Piper TTS Bettany Clone | `⚡ Experimental` | Local neural TTS model (`en_GB-alan-medium.onnx`) with Edge-TTS auto-fallback. |

---

## 🗂️ Project Structure

```
Jarvis/
├── assets/
│   ├── icons/               # Multi-resolution J.A.R.V.I.S. application icons (.ico)
│   ├── models/              # MediaPipe gesture recognizer task bundle (.task)
│   ├── security/            # User voiceprint templates & biometric configs (.npy, .json)
│   └── sounds/              # Synthesized Iron Man acoustic sound effects (.wav)
├── ai_brain/
│   ├── ai_brain.py          # Ollama local LLM interface (LLaMA 3.1:8b)
│   ├── ai_modes.py          # Personality mode definitions
│   └── brain.py             # Memory & entity context resolution
├── background_tasks/
│   ├── battery_monitor.py   # Proactive AC/DC power listener
│   ├── focus_guard.py       # Deep work distraction enforcer
│   ├── reminder_manager.py  # Asynchronous timer and reminder scheduler
│   ├── sentry_guard.py      # OpenCV Haar Cascade webcam desk presence sentinel
│   └── wellness_monitor.py  # Continuous screen-time & hydration monitor
├── command_system/
│   ├── automation.py        # Task plans and system automation handler
│   ├── command_splitter.py  # Multi-command conjunction splitter & verb inheritance
│   ├── detect_math_expression.py # Word-to-operator arithmetic engine
│   └── intent_router.py     # Intent classification (system, math, time, browser, ai)
├── core/
│   ├── assistant.py         # Main event loop, command worker & proactive services
│   ├── lifecycle.py         # Graceful shutdown & hardware release coordinator
│   ├── logger.py            # Unified structured logging engine
│   └── skill_manager.py     # Dynamic modular skill discovery & priority dispatcher
├── gui/
│   ├── gui.py               # Clean coordinator shell (~450 lines)
│   ├── tray_manager.py      # Windows System Tray notification area integration
│   └── panels/              # Modular HUD Panel Components
│       ├── __init__.py      # Package exports
│       ├── controls_panel.py# Hardware sliders, vision, diagnostics & RAM purge
│       ├── environment_panel.py # Real-time clock & live weather fetcher
│       ├── media_panel.py   # Live track metadata polling & controls
│       ├── reactor_panel.py # Arc Reactor, Radar Compass & 36-band FFT equalizer
│       ├── telemetry_panel.py # CPU/RAM radial gauges, purge button, badges
│       └── todo_panel.py    # Stark Taskmaster SQLite checklist
├── memory_layer/
│   ├── fact_extractor.py    # Structured memory extraction
│   ├── memory.py            # JSON conversational persistence
│   └── sqlite_memory.py     # SQLite structured relational storage
├── skills/                  # 42 Modular Voice & Automation Skills
│   ├── briefing_skill.py    # Tony Stark executive morning briefing
│   ├── coding_skill.py      # Developer AI Copilot
│   ├── diagnostics_skill.py # Mark VII hardware telemetry
│   ├── gesture_skill.py     # Hand gesture control toggles & camera HUD
│   ├── maid_skill.py        # Maid protocol deduplicator
│   ├── research_skill.py    # Autonomous Deep Research agent
│   ├── sentry_skill.py      # Desk Sentinel & Workstation Lock
│   ├── system_info_skill.py # System telemetry & RAM purge
│   ├── todo_skill.py        # Stark Taskmaster directives
│   ├── youtube_skill.py     # YouTube search query extractor
│   └── ...                  # 32+ additional system & media skills
├── system_layer/
│   ├── briefing_controller.py   # Morning briefing compiler
│   ├── diagnostics_controller.py# Hardware telemetry profiler
│   ├── gesture_controller.py    # MediaPipe hand tracker & OpenCV viewfinder
│   ├── maid_controller.py       # File deduplicator & organizer
│   ├── system_control.py        # Operating system controls & Windows PSAPI purge
│   ├── weather_controller.py    # Multi-tier resilient weather controller
│   └── web_agent.py             # Live web intelligence scraper
├── tests/                   # Automated Unit Test Suite (29 Passing Tests)
│   ├── test_all_commands.py # Verifies all 42 skills, intent router & command splitter
│   ├── test_gesture_control.py # Tests pinch distance logic, state transitions & skills
│   ├── test_lifecycle_logger.py# Tests shutdown hooks, logger severity & listeners
│   ├── test_memory_purge.py # Tests Windows PSAPI working-set memory optimizer
│   ├── test_modular_panels.py  # Tests decoupled CustomTkinter panel interfaces
│   ├── test_skills.py       # Tests skill manager priority ordering & routing
│   ├── test_voice_normalization.py # Tests symbol mapping and speech filters
│   └── test_weather.py      # Tests multi-tier zero-key weather fallback
├── voice_engine/
│   ├── piper_engine.py      # Offline Piper TTS wrapper (Paul Bettany clone)
│   ├── sound_effects.py     # Synthesized audio effects player
│   └── voice.py             # Audio dispatch & speech routing
├── wake_word.py             # Local ONNX wake word detection engine
├── main.py                  # Entrypoint bootstrap
├── Launch_JARVIS.vbs        # 1-Click invisible standalone background launcher
├── Stop_JARVIS.bat          # 1-Click clean process terminator
└── requirements.txt         # Python dependencies
```

---

## ⚡ Quickstart & Installation

### Prerequisites
1. **Windows 10 or 11** (64-bit)
2. **Python 3.11+** installed and added to `PATH`
3. *(Optional for Local AI)* **Ollama** installed:
   ```bash
   ollama pull llama3.1:8b
   ollama pull gemma:2b
   ```

### 1. Clone & Set Up Virtual Environment
```powershell
git clone https://github.com/Pothinasreeram/Jarvis.git
cd Jarvis

# Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration (Zero-Key by Default)
J.A.R.V.I.S. runs out-of-the-box with **zero required API keys**!
* Weather resolves automatically via the public Open-Meteo API.
* Speech synthesis auto-routes to high-fidelity Edge-TTS or local SAPI5.

If you wish to configure optional third-party integrations (such as Spotify or Tomorrow.io), copy the example configuration:
```powershell
cp .env.example .env
```
> **Security Note:** `.env` is permanently excluded via `.gitignore` to prevent secret exposure. Never commit personal keys.

### 3. Run the Automated Test Suite
Verify your installation and subsystem integrity before running:
```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

### 4. Launch J.A.R.V.I.S.
* **Standard Launch (Console + HUD):**
  ```powershell
  python main.py
  ```
* **Standalone Desktop Launcher:**
  Double-click `Launch_JARVIS.vbs` for a borderless standalone desktop experience with System Tray integration.
* **Stop Application:**
  Run `Stop_JARVIS.bat` to terminate all background daemons cleanly.

---

## 🗣️ Voice Directive Cheat-Sheet

| Category | Voice / Console Command | Result |
| :--- | :--- | :--- |
| **Morning Briefing** | `"good morning"` / `"morning briefing"` | Executive audio brief: weather, tasks, hardware, headlines & water. |
| **Developer Copilot** | `"write python code to scrape a website"` | Generates production code with LLaMA and saves to Desktop. |
| **YouTube Search** | `"search youtube for lo-fi beats"` | Extracts query and opens YouTube search results in browser. |
| **Hardware Diagnostics** | `"system diagnostics"` / `"mark vii status"` | Complete hardware profile (CPU GHz, RAM, GPU, thermals, health index). |
| **Hand Gestures** | `"activate gesture control"` / `"turn on gestures"` | Enables webcam neural hand tracking for air volume & speech interrupts. |
| **Desk Sentinel** | `"activate sentry mode"` / `"lock workstation"` | Arms webcam face detection; auto-locks Windows when you walk away. |
| **Voice Biometrics** | `"enroll voiceprint"` / `"verify voiceprint"` | Calibrates and authenticates your unique acoustic voice timbre. |
| **Autonomous Research** | `"research <topic>"` | Synthesizes a 4-section executive brief & saves Markdown to Desktop. |
| **Tech Intelligence** | `"tech news"` / `"hacker news"` | Speaks the top trending stories from the Hacker News API. |
| **Task Directives** | `"add task <directive>"` / `"what are my tasks"` | Logs to SQLite and updates HUD checklist in real time. |
| **Wellness & Posture** | `"log a glass of water"` / `"posture check"` | Increments daily water count; provides 20-20-20 ergonomic stretch advice. |
| **Work Protocols** | `"activate work protocol"` / `"gaming mode"` | Automates window snapping, volume, brightness, and deep work timers. |
| **Maid Protocol** | `"maid protocol"` / `"clean downloads"` | Automatically organizes folders and purges duplicate files. |
| **Music Playback** | `"play <song name> on spotify"` | Hands-free Spotify media playback. |
| **HUD Summon** | `Ctrl + Space` (Global Hotkey) | Instantly brings J.A.R.V.I.S. to the foreground or minimizes to Tray. |

---

## 👨‍💻 Author & Acknowledgments

* **Architect & Developer:** [Pothina Sreeram](https://github.com/Pothinasreeram)
* **Inspiration:** J.A.R.V.I.S. from Marvel's *Iron Man*
* **Special Thanks:** CustomTkinter, Ollama, OpenWakeWord, and Rhasspy Piper teams.

---

<p align="center">
  <i>"Sometimes you gotta run before you can walk." — Tony Stark</i>
</p>
