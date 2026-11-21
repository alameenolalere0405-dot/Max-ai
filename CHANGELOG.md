# MAX AI — Changelog
**LEREON Technologies — MAX AI © 2026 LEREON Technologies. All rights reserved.**

---

## [2.0.0] — 2026

### Added
- **Complete UI redesign** — futuristic HUD interface with animated neural mesh sphere, segmented rings, scanner sweep, HUD data readouts
- **Slim icon nav rail** — 56px navigation with tooltip labels; content panels hidden until needed (not cluttered)
- **First-launch setup wizard** — 7-step onboarding: welcome, provider selection, API key entry, live connection verification, permissions, personalization, done
- **Secure API key storage** — OS Keyring (Windows Credential Manager / macOS Keychain / Linux SecretService) with Fernet-encrypted file fallback
- **Unified database** (core/database.py) — single SQLite with schema migrations, conversations, messages, facts, audit log, full-text search
- **Streaming responses** — OpenAI, Anthropic, Groq providers now stream tokens as they arrive
- **Conversation sidebar** — new chat, search, rename, delete conversations
- **Ollama cloud support** — configurable cloud endpoint with Bearer token authentication, alongside local Ollama
- **Multi-model collaboration dialog** — select 2–4 providers for Research → Analysis → Review → Synthesis pipeline
- **MAX Studio** — 12 task types, file reading (PDF/DOCX/XLSX/TXT/MD), save output
- **MAX Knowledge Base** — import documents, keyword search with relevance ranking, context auto-injection
- **MAX Productivity** — todos with priority/due dates, notes with full-text search, reminders
- **Workflow automation** — trigger types: manual, scheduled, keyword, startup; safe action allowlist
- **System monitor** — real-time CPU/RAM/disk/battery/network, top processes, health score
- **Personality engine** — 6 modes (Professional/Friendly/Sarcastic/Savage/Nerdy/Creative), sarcasm slider 0–100
- **Plugin system** — load/unload .py plugins at runtime, documented API, example template
- **Desktop control** — 20-app safe allowlist, file navigation, clipboard, keyboard shortcuts (all with confirmation)
- **Vision engine** — screenshots, AI image analysis (OpenAI/Anthropic/Gemini), OCR, camera capture, hand gesture detection
- **Voice engine** — STT (Google + Whisper fallback), TTS (pyttsx3), push-to-talk, wake word ("Hey MAX")
- **GitHub Actions CI/CD** — test on Python 3.10/3.11/3.12, Windows/macOS/Linux native builds, checksums, release publishing
- **PyInstaller build script** — Windows .exe, macOS .dmg (universal2), Linux AppImage + .deb
- **124 automated tests** — covers all 13 modules including 10 issue-specific regression tests
- **Complete documentation** — README, INSTALLATION, USER_GUIDE, API_SETUP, SECURITY, PRIVACY, TROUBLESHOOTING, CHANGELOG, CONTRIBUTING, RELEASE

### Fixed
- Monitor callback thread safety — UI updates now dispatched via `QTimer.singleShot(0)`
- Voice input thread safety — transcript dispatch via `QTimer.singleShot(0)`
- Microphone, camera, screen_capture, automation, notifications all default OFF
- API keys never written to `config.json` — stay in `.env` or secure storage
- Config persistence — all provider, personality, permission changes survive restart
- Ollama cloud settings persist through config save/reload cycle
- Memory pruning respects max_history limit correctly
- Settings dialog includes all Ollama cloud fields

### Changed
- Branding updated from AOA Digital to **LEREON Technologies** throughout
- Main window redesigned from 3-panel layout to icon-rail + content stack
- Settings moved inline to main window Settings view + full dialog option
- Sphere widget upgraded with neural mesh, scanner sweep, HUD corner readouts

---

## [1.0.0] — 2025

### Added
- Initial release
- PyQt6 GUI with animated sphere
- Multi-provider AI support (OpenAI, Anthropic, Gemini, Groq, DeepSeek, Mistral, OpenRouter, Ollama)
- Basic chat interface
- Memory engine (SQLite)
- Voice engine (STT/TTS)
- Knowledge base
- Productivity tools
- Workflow automation
- System monitor
- Plugin system
- Personality engine
