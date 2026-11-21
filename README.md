# MAX AI — Modular Autonomous eXecutive
### LEREON Technologies
**MAX AI © 2026 LEREON Technologies. All rights reserved.**

---

## Overview

MAX AI is a private-first personal desktop AI assistant with a distinctive personality — intelligent, witty, and sarcastic by default. It runs on Windows, macOS, and Linux with a futuristic dark PyQt6 GUI and supports eight AI providers simultaneously.

This document describes features that are **implemented and tested**. It does not describe planned features.

---

## Quick Start

```bash
# 1. First-time setup
python setup.py

# 2. Launch GUI
python main.py

# 3. Terminal mode (no GUI required)
python main.py --cli

# 4. Run automated tests
python tests/test_max.py

# 5. System diagnostics
python main.py --diagnose
```

---

## Implemented Features

### AI Providers
Eight providers supported. Switch between them from the sidebar dropdown or Settings.

| Provider | Auth | Notes |
|----------|------|-------|
| OpenAI | API key | GPT-4o, o1, etc. |
| Anthropic | API key | Claude Opus, Sonnet, Haiku |
| Google Gemini | API key | gemini-1.5-pro etc. |
| Groq | API key | llama3-70b-8192 etc. |
| DeepSeek | API key | Uses OpenAI-compatible API |
| Mistral | API key | mistral-large-latest etc. |
| OpenRouter | API key | Gateway to 100+ models |
| Ollama Local | None | Requires `ollama serve` running |
| Ollama Cloud | Bearer token | Custom cloud endpoint + optional API key |

Provider switching takes effect immediately in the sidebar dropdown. Model names are configurable per provider in Settings → API Keys.

### Multi-Model Collaboration
Accessible via the **🤝 Multi-Model Collaborate** button above the chat. Select 2–4 enabled providers. Each contributes in sequence: Research → Analysis → Review → Synthesis. Results shown per-model in a dedicated dialog.

Requires at least 2 providers with valid API keys configured.

### MAX Recall (Memory)
- SQLite database at `memory/max.db`
- Stores conversation exchanges automatically (when memory permission is on)
- Retrieves recent context and injects it into each AI request
- Separate facts table for key/value user preferences
- Clear all history from Settings → Memory
- Max history configurable (default: 50 turns)
- API keys are **never** written to config.json — they stay in `.env`

### Voice Assistant
Voice features require packages listed below and permissions enabled in Settings.

| Feature | Status | Requires |
|---------|--------|----------|
| Push-to-talk (mic button in chat) | Implemented | `SpeechRecognition`, `pyaudio` |
| Google STT (online) | Implemented | Internet + `SpeechRecognition` |
| Whisper STT (local, offline) | Implemented (fallback) | `openai-whisper`, `torch` |
| Text-to-speech output | Implemented | `pyttsx3` |
| Wake word "Hey MAX" | Implemented | `pvporcupine` + Picovoice key |
| Continuous conversation mode | Implemented via sidebar Listen button | Same as above |

**Note:** Microphone permission is **off by default**. Enable in Settings → Permissions.

### MAX Vision
| Feature | Status | Requires |
|---------|--------|----------|
| Screenshot capture | Implemented | `mss` or `Pillow` (screen_capture permission) |
| AI image analysis | Implemented | Vision-capable provider (GPT-4o, Claude, Gemini) |
| OCR text extraction | Implemented | `pytesseract` + Tesseract binary |
| Camera frame capture | Implemented | `opencv-python` + camera permission |
| Hand gesture detection | Implemented | `opencv-python` + `mediapipe>=0.10` + camera permission |

**Gesture actions:** open palm = pause, thumbs up = confirm, point = navigate, peace = secondary action, fist = stop.

**Note:** Camera permission is **off by default**. Enable in Settings → Permissions.

### MAX Studio
Access via the Studio tab. Paste content or load a file, select a task type, and send to MAX.

Implemented task types: `summarize`, `code_review`, `write_docs`, `readme`, `explain`, `refactor`, `unit_tests`, `presentation_outline`, `report`, `email_draft`, `meeting_summary`, `custom`.

File reading: `.txt`, `.md`, `.py`, `.json`, `.csv`, `.html`, `.pdf` (requires PyPDF2), `.docx` (requires python-docx), `.xlsx`/`.xls` (requires openpyxl).

Output can be saved to any location via the Save Output button.

### MAX Productivity
Access via the Productivity tab.

- **Todos:** add with title and priority (Low/Medium/High), mark complete by double-clicking, filtered active/done view
- **Notes:** title + content, full-text search, timestamp tracking
- **Reminders:** set a future time, checked every 30 seconds, shown as a dialog when due

All stored in SQLite at `memory/productivity.db`.

### MAX Knowledge Base
Access via the Knowledge Base tab.

- Import: `.pdf`, `.txt`, `.md`, `.docx`, `.py`, `.json`, `.csv`, `.html`
- Duplicate detection by SHA-256 hash
- Keyword search with relevance ranking
- Context injection: relevant snippets automatically added to AI prompts when you ask about imported topics
- Delete documents individually via right-click

### MAX Automate
Access via the Automation tab.

- Create workflows with Trigger + Steps
- Trigger types: Manual, Schedule (daily HH:MM), Keyword (fires when chat contains keyword), Startup
- Action types: Chat message, Open app, Notify, Web search, Clipboard copy, System info, Speak, Wait
- All actions use a safe allowlist — no arbitrary shell execution
- Sensitive actions require confirmation
- Workflows persisted as JSON in `tasks/workflows.json`
- Scheduler runs in background checking every 60 seconds

### System Monitor
Access via the Monitor tab.

- Real-time CPU %, RAM %, disk %, battery (where available), network speed
- Refreshed every 2.5 seconds via background thread
- Top 8 processes by CPU usage
- Health score (0–100)
- All UI updates dispatched to main thread via QTimer.singleShot(0) — thread-safe

Requires `psutil`.

### Personality Engine
Controlled from the sidebar.

| Mode | Behaviour |
|------|-----------|
| Professional | Polished, precise, no humor |
| Friendly | Warm, encouraging |
| Sarcastic (default) | Dry wit, clever observations |
| Savage | Blunt, no sugar-coating |
| Nerdy | Technical enthusiasm, programming references |
| Creative | Imaginative, expressive |

Sarcasm intensity: 0 (off) → 100 (maximum) via sidebar slider. Setting 0 disables all humor. `force_serious` in config overrides everything.

### Plugin System
Drop a `.py` file into `plugins/installed/` and load it from MAX menu → Plugins.

Each plugin must define a class `Plugin` inheriting from `BasePlugin` with a `meta` property and `on_load(core)` method. See `plugins/installed/*.py.template` for the full documented template.

Loaded plugins can post-process chat responses via `on_chat_message()` and register additional tools via `get_tools()`.

### Desktop Control
Triggered via Quick Actions sidebar or natural language in chat.

Safe operations (no arbitrary command execution):
- Launch apps from a fixed allowlist of 20 named apps
- List directory contents
- Find files by name pattern
- Open a file with its default app
- Get/set clipboard
- Get system info
- Send safe keyboard shortcuts (copy, paste, undo, etc.)

All launch and open operations call a confirmation callback before executing. PC Control permission must be enabled in Settings (off by default).

---

## Permissions

All sensitive permissions are **off by default**. Enable them in Settings → Permissions.

| Permission | Default | What it enables |
|------------|---------|-----------------|
| web_browsing | ✅ ON | Web fetch and search tools |
| file_read | ✅ ON | File reading tools |
| memory | ✅ ON | Conversation memory persistence |
| file_write | ❌ OFF | Writing files to disk |
| screen_capture | ❌ OFF | Screenshots |
| microphone | ❌ OFF | Voice input |
| camera | ❌ OFF | Camera capture and gestures |
| pc_control | ❌ OFF | App launching, file opening |
| notifications | ❌ OFF | System notifications |
| automation | ❌ OFF | Automated workflow execution |

---

## Configuration

### API Keys
Store in `.env` (created from `.env.template` by setup.py). Never committed to version control. API keys are never written to `config.json`.

```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...
GROQ_API_KEY=gsk_...
DEEPSEEK_API_KEY=...
MISTRAL_API_KEY=...
OPENROUTER_API_KEY=...
PICOVOICE_ACCESS_KEY=...
OLLAMA_BASE_URL=http://localhost:11434
```

### Ollama Cloud
In Settings → API Keys → Ollama:
- Enable "Use cloud endpoint"
- Set Cloud URL (e.g. `https://my-ollama.example.com`)
- Set Cloud API Key (Bearer token, optional for public endpoints)

Local and cloud Ollama both use `/api/chat` with fallback to `/api/generate` for older versions.

### Config file
`config/config.json` — edited automatically by Settings dialog. All changes persist across restarts. Contains no API keys.

---

## Command-Line Options

```
python main.py                       # GUI (default)
python main.py --cli                 # Terminal chat
python main.py --setup               # Re-run setup wizard
python main.py --diagnose            # System health check
python main.py --test                # Run test suite
python main.py --provider openai     # Force a specific provider
python main.py --voice               # Start with voice active
python main.py --debug               # Verbose logging
python main.py --version             # Print version
```

---

## Test Results

```
Ran 124 tests in ~3 seconds

OK (0 failures, 0 errors)
```

Test coverage includes: config loading and persistence, all 10 tools, memory engine (SQLite, store/retrieve/prune/facts), all 6 personality modes, knowledge base (import/search/delete/context), productivity (todos/notes/reminders), automation (create/run/persist/enable/keyword), plugins, system monitor, studio engine (12 task types, file reading, save), vision engine, desktop control (permissions, confirmation, safe apps), diagnostics, and all 10 issue-specific regression tests.

**Tests that require API keys:** provider connection and streaming (not in automated suite — requires live credentials)
**Tests that require hardware:** camera, microphone, gesture recognition (gracefully skipped if hardware unavailable)

---

## Project Structure

```
max_ai/
├── main.py                        # Entry point (all CLI flags)
├── setup.py                       # First-time setup wizard
├── requirements.txt               # Python dependencies
├── .env                           # API keys (create from .env.template)
├── .env.template                  # Key template — safe to commit
├── config/config.json             # App configuration (no secrets)
│
├── core/
│   ├── config.py                  # Config loader, .env injection, save/reload
│   ├── max_core.py                # Central coordinator, all subsystems
│   ├── cli_mode.py                # Terminal interface
│   ├── desktop_control.py         # Safe PC operations, SAFE_APPS allowlist
│   └── diagnostics.py             # 7-category system self-check
│
├── providers/
│   ├── router.py                  # Dynamic provider selection, fallback
│   ├── openai_provider.py         # OpenAI (also DeepSeek, OpenRouter)
│   ├── anthropic_provider.py      # Anthropic Claude
│   ├── gemini_provider.py         # Google Gemini
│   ├── groq_provider.py           # Groq
│   ├── mistral_provider.py        # Mistral AI
│   └── ollama_provider.py         # Ollama local + cloud with Bearer auth
│
├── ui/
│   ├── main_window.py             # Full dashboard (tabs, sidebar, monitor)
│   ├── core_widget.py             # Animated energy sphere (60 fps, 11 states)
│   ├── chat_widget.py             # Chat with markdown, thread-safe voice
│   ├── settings_dialog.py         # All settings including Ollama cloud
│   ├── collaborate_dialog.py      # Multi-model collaboration
│   ├── plugin_dialog.py           # Plugin manager
│   └── theme.py                   # Global dark theme stylesheet
│
├── tools/all_tools.py             # 10 built-in tools + ToolRegistry
├── memory/memory_engine.py        # SQLite conversation memory + facts
├── voice/voice_engine.py          # STT, TTS, wake word, push-to-talk
├── vision/vision_engine.py        # Screenshots, OCR, AI analysis, gestures
├── personality/personality_engine.py  # 6 modes, sarcasm 0-100
├── studio/studio_engine.py        # 12 task templates, file reading
├── knowledge/knowledge_base.py    # Document import, search, context injection
├── productivity/productivity_engine.py  # Todos, notes, reminders
├── automation/workflow_engine.py  # Trigger/action workflows, scheduler
├── monitor/system_monitor.py      # Real-time system stats (background thread)
├── tasks/task_manager.py          # Task state tracking
├── plugins/
│   ├── plugin_manager.py          # Load/unload plugins at runtime
│   └── installed/                 # Drop .py plugin files here
│
├── tests/test_max.py              # 124 automated tests
├── logs/                          # max.log, rotating
├── memory/                        # max.db, knowledge.db, productivity.db
└── uploads/                       # Screenshots, camera frames
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| "No AI providers available" | Add at least one API key to `.env`, restart |
| Voice input not working | Install `pyaudio` + `SpeechRecognition`, enable Microphone in Settings |
| pyaudio fails on macOS | `brew install portaudio && pip install pyaudio` |
| pyaudio fails on Ubuntu | `sudo apt-get install portaudio19-dev && pip install pyaudio` |
| Screenshots failing | Install `mss`, enable Screen Capture in Settings |
| Gesture control not working | `pip install opencv-python mediapipe>=0.10`, enable Camera |
| PDF reading empty | Install `PyPDF2`: `pip install PyPDF2` |
| Provider error 401 | API key invalid or expired — update in Settings or `.env` |
| Config not persisting | Check write permissions on `config/config.json` |

Run `python main.py --diagnose` for a full status report with actionable fixes.

---

*MAX AI © 2026 LEREON Technologies. All rights reserved.*
