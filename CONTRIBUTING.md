# MAX AI — Contributing Guide
**LEREON Technologies — MAX AI © 2026 LEREON Technologies. All rights reserved.**

---

## Development Setup

```bash
git clone https://github.com/lereontech/max-ai.git
cd max-ai
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows
python setup.py
python main.py
```

## Running Tests

```bash
python tests/test_max.py
```

All 124 tests must pass before submitting a PR.

## Code Standards

- Python 3.10+ syntax only
- Type hints on all public functions
- Docstrings on all classes and public methods
- No hardcoded API keys or secrets
- All sensitive actions require user confirmation
- Thread-safe UI updates via `QTimer.singleShot(0)`
- New features need tests in `tests/test_max.py`

## Module Architecture

```
core/        — Config, MAXCore, Database, SecureStorage, Desktop, Diagnostics, CLI
providers/   — One file per AI provider, all inherit BaseProvider
tools/       — All tools in all_tools.py, inherit BaseTool
ui/          — PyQt6 widgets only, no business logic
memory/      — MemoryEngine wraps core/database.py
voice/       — VoiceEngine (STT + TTS + wake word)
vision/      — VisionEngine (screenshots, OCR, gestures)
personality/ — PersonalityEngine (modes + sarcasm)
knowledge/   — KnowledgeBase (document import + search)
studio/      — StudioEngine (writing + file tasks)
productivity/— ProductivityEngine (todos, notes, reminders)
automation/  — WorkflowEngine (triggers + actions)
monitor/     — SystemMonitor (background stats thread)
tasks/       — TaskManager (state tracking)
plugins/     — PluginManager + installed/
tests/       — test_max.py (124 tests)
```

## Adding a New AI Provider

1. Create `providers/myprovider_provider.py` inheriting `BaseProvider`.
2. Implement `complete()` and optionally `stream()` and `list_models()`.
3. Add a `_load_myprovider()` method in `providers/router.py`.
4. Add config fields in `config/config.json` under `providers`.
5. Add to the settings dialog `PROVIDERS` list in `ui/settings_dialog.py`.
6. Add to `PROVIDERS_INFO` in `ui/onboarding.py`.
7. Write tests in `tests/test_max.py`.

## Adding a New Tool

1. Add a class inheriting `BaseTool` in `tools/all_tools.py`.
2. Set `name`, `description`, `permission_key`.
3. Implement `async def run(self, **kwargs) -> str`.
4. Register it in `ToolRegistry._register_defaults()`.
5. Write tests.

## Adding a Plugin

See `plugins/installed/*.py.template` for the documented plugin API.

## Security Rules

- Never execute arbitrary shell commands.
- Never write to user files without explicit permission.
- Never store API keys in config.json or logs.
- Always confirm destructive or irreversible operations.
- Always validate file paths before reading or writing.

## Pull Request Checklist

- [ ] All 124 existing tests pass
- [ ] New tests added for new functionality
- [ ] No hardcoded secrets
- [ ] No syntax errors (`python -c "import ast; ast.parse(open('file.py').read())"`)
- [ ] Thread-safe UI updates
- [ ] Docstrings on new public classes/functions
- [ ] CHANGELOG.md updated
- [ ] README.md updated if needed
