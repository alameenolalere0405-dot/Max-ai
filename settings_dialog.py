"""MAX AI — Settings Dialog"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QLineEdit, QCheckBox, QComboBox, QPushButton,
    QFormLayout, QScrollArea, QFrame, QMessageBox, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class SettingsDialog(QDialog):
    settings_saved = pyqtSignal()

    PROVIDERS = [
        ("openai",     "OpenAI",      "api_key", "model", "GPT-4o"),
        ("anthropic",  "Anthropic",   "api_key", "model", "claude-opus-4-5"),
        ("gemini",     "Gemini",      "api_key", "model", "gemini-1.5-pro"),
        ("groq",       "Groq",        "api_key", "model", "llama3-70b-8192"),
        ("deepseek",   "DeepSeek",    "api_key", "model", "deepseek-chat"),
        ("mistral",    "Mistral",     "api_key", "model", "mistral-large-latest"),
        ("openrouter", "OpenRouter",  "api_key", "model", "openai/gpt-4o"),
    ]

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("MAX AI — Settings")
        self.setMinimumSize(640, 520)
        self.setModal(True)
        self._fields: dict[str, QWidget] = {}
        self._build_ui()
        self._load_values()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # Title bar
        title = QLabel("  ⚙  SETTINGS")
        title.setStyleSheet(
            "background:#030C18; color:#00BFFF; font-size:13px; font-weight:bold;"
            "padding:12px; border-bottom:1px solid #0A2A45;"
        )
        layout.addWidget(title)

        # Tabs
        tabs = QTabWidget()
        tabs.setContentsMargins(8, 8, 8, 8)
        tabs.addTab(self._build_providers_tab(), "API Keys")
        tabs.addTab(self._build_permissions_tab(), "Permissions")
        tabs.addTab(self._build_voice_tab(), "Voice")
        tabs.addTab(self._build_memory_tab(), "Memory")
        layout.addWidget(tabs, 1)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(12, 8, 12, 12)
        btn_row.addStretch()
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        save = QPushButton("Save Settings")
        save.setObjectName("accent_btn")
        save.clicked.connect(self._save)
        btn_row.addWidget(cancel)
        btn_row.addWidget(save)
        layout.addLayout(btn_row)

    # ── Providers tab ─────────────────────────────────────────────────────

    def _build_providers_tab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        vl = QVBoxLayout(container)
        vl.setSpacing(10)
        vl.setContentsMargins(12, 12, 12, 12)

        note = QLabel("API keys are stored in your local <b>.env</b> file and never transmitted anywhere except to the respective provider.")
        note.setWordWrap(True)
        note.setStyleSheet("color:#4090B0; font-size:11px; padding:6px 0;")
        vl.addWidget(note)

        for pid, label, key_field, model_field, default_model in self.PROVIDERS:
            group = QGroupBox(label)
            group.setStyleSheet(
                "QGroupBox { color:#00BFFF; border:1px solid #0A2A45; border-radius:6px;"
                "margin-top:8px; padding:8px; font-size:12px; font-weight:bold;}"
                "QGroupBox::title { subcontrol-origin:margin; left:8px; padding:0 4px;}"
            )
            fl = QFormLayout(group)
            fl.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
            fl.setSpacing(6)

            # Enabled checkbox
            enabled_cb = QCheckBox("Enable")
            enabled_cb.setObjectName(f"{pid}_enabled")
            self._fields[f"{pid}_enabled"] = enabled_cb
            fl.addRow("", enabled_cb)

            # API key
            key_input = QLineEdit()
            key_input.setObjectName(f"{pid}_api_key")
            key_input.setPlaceholderText(f"Enter {label} API key…")
            key_input.setEchoMode(QLineEdit.EchoMode.Password)
            self._fields[f"{pid}_api_key"] = key_input
            fl.addRow("API Key:", key_input)

            # Model
            model_input = QLineEdit()
            model_input.setObjectName(f"{pid}_model")
            model_input.setPlaceholderText(default_model)
            self._fields[f"{pid}_model"] = model_input
            fl.addRow("Model:", model_input)

            vl.addWidget(group)

        # Ollama — local + cloud
        group = QGroupBox("Ollama (Local or Cloud)")
        group.setStyleSheet(
            "QGroupBox { color:#00BFFF; border:1px solid #0A2A45; border-radius:6px;"
            "margin-top:8px; padding:8px; font-size:12px; font-weight:bold;}"
            "QGroupBox::title { subcontrol-origin:margin; left:8px; padding:0 4px;}"
        )
        fl = QFormLayout(group)
        fl.setSpacing(6)
        enabled_cb = QCheckBox("Enable")
        enabled_cb.setObjectName("ollama_enabled")
        self._fields["ollama_enabled"] = enabled_cb
        fl.addRow("", enabled_cb)

        url_input = QLineEdit()
        url_input.setObjectName("ollama_base_url")
        url_input.setPlaceholderText("http://localhost:11434")
        self._fields["ollama_base_url"] = url_input
        fl.addRow("Local URL:", url_input)

        model_input = QLineEdit()
        model_input.setObjectName("ollama_model")
        model_input.setPlaceholderText("llama3")
        self._fields["ollama_model"] = model_input
        fl.addRow("Model:", model_input)

        cloud_cb = QCheckBox("Use cloud endpoint instead of local")
        cloud_cb.setObjectName("ollama_use_cloud")
        self._fields["ollama_use_cloud"] = cloud_cb
        fl.addRow("", cloud_cb)

        cloud_url_input = QLineEdit()
        cloud_url_input.setObjectName("ollama_cloud_url")
        cloud_url_input.setPlaceholderText("https://your-ollama-cloud.example.com")
        self._fields["ollama_cloud_url"] = cloud_url_input
        fl.addRow("Cloud URL:", cloud_url_input)

        cloud_key_input = QLineEdit()
        cloud_key_input.setObjectName("ollama_api_key")
        cloud_key_input.setPlaceholderText("Bearer token for cloud auth (leave blank for local)")
        cloud_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._fields["ollama_api_key"] = cloud_key_input
        fl.addRow("Cloud API Key:", cloud_key_input)

        note = QLabel("Local Ollama requires 'ollama serve' running. Cloud requires a URL + optional Bearer token.")
        note.setStyleSheet("color:#2A6080; font-size:10px;")
        note.setWordWrap(True)
        fl.addRow("", note)
        vl.addWidget(group)
        vl.addStretch()

        scroll.setWidget(container)
        return scroll

    # ── Permissions tab ───────────────────────────────────────────────────

    def _build_permissions_tab(self) -> QWidget:
        w = QWidget()
        vl = QVBoxLayout(w)
        vl.setContentsMargins(16, 16, 16, 16)
        vl.setSpacing(8)

        perms = [
            ("web_browsing",   "Web Browsing — allow MAX to fetch and search the web"),
            ("file_read",      "File Read — allow MAX to read files you specify"),
            ("file_write",     "File Write — allow MAX to create/modify files (use with care)"),
            ("screen_capture", "Screen Capture — allow MAX to take screenshots"),
            ("pc_control",     "PC Control — allow MAX to launch apps (requires confirmation)"),
            ("microphone",     "Microphone — allow voice input"),
            ("camera",         "Camera — allow webcam access"),
            ("notifications",  "Notifications — allow MAX to send system notifications"),
            ("automation",     "Automation — allow automated repetitive tasks"),
            ("memory",         "Memory — persist conversation context between sessions"),
        ]

        note = QLabel("All sensitive actions still require confirmation regardless of these settings.")
        note.setStyleSheet("color:#4090B0; font-size:11px; margin-bottom:8px;")
        note.setWordWrap(True)
        vl.addWidget(note)

        for key, desc in perms:
            cb = QCheckBox(desc)
            cb.setObjectName(f"perm_{key}")
            self._fields[f"perm_{key}"] = cb
            vl.addWidget(cb)

        vl.addStretch()
        return w

    # ── Voice tab ─────────────────────────────────────────────────────────

    def _build_voice_tab(self) -> QWidget:
        w = QWidget()
        vl = QVBoxLayout(w)
        vl.setContentsMargins(16, 16, 16, 16)
        vl.setSpacing(10)

        vi = QCheckBox("Enable voice input (microphone → speech-to-text)")
        vi.setObjectName("voice_input")
        self._fields["voice_input"] = vi
        vl.addWidget(vi)

        vo = QCheckBox("Enable voice output (MAX speaks responses aloud)")
        vo.setObjectName("voice_output")
        self._fields["voice_output"] = vo
        vl.addWidget(vo)

        ww = QCheckBox("Enable wake word — say 'Hey MAX' to activate listening")
        ww.setObjectName("wake_word")
        self._fields["wake_word"] = ww
        vl.addWidget(ww)

        note = QLabel(
            "Voice input requires: <b>pyaudio</b> and <b>SpeechRecognition</b><br>"
            "Wake word requires: <b>pvporcupine</b> and a free Picovoice account key<br>"
            "Voice output requires: <b>pyttsx3</b>"
        )
        note.setStyleSheet("color:#4090B0; font-size:11px; margin-top:12px;")
        note.setWordWrap(True)
        vl.addWidget(note)
        vl.addStretch()
        return w

    # ── Memory tab ────────────────────────────────────────────────────────

    def _build_memory_tab(self) -> QWidget:
        w = QWidget()
        vl = QVBoxLayout(w)
        vl.setContentsMargins(16, 16, 16, 16)
        vl.setSpacing(10)

        mem_on = QCheckBox("Enable memory (persist conversation context between sessions)")
        mem_on.setObjectName("memory_enabled")
        self._fields["memory_enabled"] = mem_on
        vl.addWidget(mem_on)

        fl = QFormLayout()
        max_h = QLineEdit()
        max_h.setObjectName("memory_max_history")
        max_h.setPlaceholderText("50")
        self._fields["memory_max_history"] = max_h
        fl.addRow("Max history turns:", max_h)
        vl.addLayout(fl)

        clear_btn = QPushButton("🗑  Clear All Memory Now")
        clear_btn.setStyleSheet("color:#FF4455; border-color:#FF4455;")
        clear_btn.clicked.connect(self._clear_memory)
        vl.addWidget(clear_btn)
        vl.addStretch()
        return w

    # ── Load / Save ───────────────────────────────────────────────────────

    def _load_values(self):
        for pid, label, _, _, _ in self.PROVIDERS:
            cfg = self.config.provider_cfg(pid)
            self._set(f"{pid}_enabled", bool(cfg.get("enabled")))
            self._set(f"{pid}_api_key", cfg.get("api_key", ""))
            self._set(f"{pid}_model",   cfg.get("model", ""))

        ollama = self.config.provider_cfg("ollama")
        self._set("ollama_enabled",   bool(ollama.get("enabled")))
        self._set("ollama_base_url",  ollama.get("base_url", "http://localhost:11434"))
        self._set("ollama_model",     ollama.get("model", "llama3"))
        self._set("ollama_use_cloud", bool(ollama.get("use_cloud", False)))
        self._set("ollama_cloud_url", ollama.get("cloud_url", ""))
        self._set("ollama_api_key",   ollama.get("api_key", ""))

        for key in ["web_browsing","file_read","file_write","screen_capture",
                    "pc_control","microphone","camera","notifications","automation","memory"]:
            self._set(f"perm_{key}", self.config.permission(key))

        self._set("voice_input",  self.config.voice_input_enabled)
        self._set("voice_output", self.config.voice_output_enabled)
        self._set("wake_word",    self.config.wake_word_enabled)
        self._set("memory_enabled", self.config.memory_enabled)
        self._set("memory_max_history", str(self.config.get("memory", "max_history", default=50)))

    def _set(self, key: str, value):
        widget = self._fields.get(key)
        if widget is None:
            return
        if isinstance(widget, QCheckBox):
            widget.setChecked(bool(value))
        elif isinstance(widget, QLineEdit):
            widget.setText(str(value) if value else "")

    def _get(self, key: str):
        widget = self._fields.get(key)
        if widget is None:
            return None
        if isinstance(widget, QCheckBox):
            return widget.isChecked()
        if isinstance(widget, QLineEdit):
            return widget.text().strip()
        return None

    def _save(self):
        import os
        env_lines = {}

        # Read existing .env
        from pathlib import Path
        ROOT = Path(__file__).parent.parent
        env_path = ROOT / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if "=" in line and not line.startswith("#"):
                    k, _, v = line.partition("=")
                    env_lines[k.strip()] = v.strip()

        ENV_MAP = {
            "openai_api_key":     "OPENAI_API_KEY",
            "anthropic_api_key":  "ANTHROPIC_API_KEY",
            "gemini_api_key":     "GOOGLE_API_KEY",
            "groq_api_key":       "GROQ_API_KEY",
            "deepseek_api_key":   "DEEPSEEK_API_KEY",
            "mistral_api_key":    "MISTRAL_API_KEY",
            "openrouter_api_key": "OPENROUTER_API_KEY",
        }

        # Save provider settings
        for pid, label, _, _, _ in self.PROVIDERS:
            enabled = bool(self._get(f"{pid}_enabled"))
            api_key = self._get(f"{pid}_api_key") or ""
            model   = self._get(f"{pid}_model") or ""
            self.config.set("providers", pid, "enabled", enabled)
            if model:
                self.config.set("providers", pid, "model", model)
            env_key = ENV_MAP.get(f"{pid}_api_key")
            if env_key and api_key:
                env_lines[env_key] = api_key

        # Ollama
        self.config.set("providers", "ollama", "enabled",   bool(self._get("ollama_enabled")))
        self.config.set("providers", "ollama", "base_url",  self._get("ollama_base_url") or "http://localhost:11434")
        self.config.set("providers", "ollama", "model",     self._get("ollama_model") or "llama3")
        self.config.set("providers", "ollama", "use_cloud", bool(self._get("ollama_use_cloud")))
        self.config.set("providers", "ollama", "cloud_url", self._get("ollama_cloud_url") or "")
        self.config.set("providers", "ollama", "api_key",   self._get("ollama_api_key") or "")

        # Permissions
        for key in ["web_browsing","file_read","file_write","screen_capture",
                    "pc_control","microphone","camera","notifications","automation","memory"]:
            self.config.set("permissions", key, bool(self._get(f"perm_{key}")))

        # Voice
        self.config.set("assistant", "voice_input_enabled",  bool(self._get("voice_input")))
        self.config.set("assistant", "voice_output_enabled", bool(self._get("voice_output")))
        self.config.set("assistant", "wake_word_enabled",    bool(self._get("wake_word")))

        # Memory
        self.config.set("memory", "enabled", bool(self._get("memory_enabled")))
        try:
            self.config.set("memory", "max_history", int(self._get("memory_max_history") or 50))
        except ValueError:
            pass

        # Write .env
        with open(env_path, "w") as f:
            for k, v in env_lines.items():
                f.write(f"{k}={v}\n")

        self.config.save()
        self.settings_saved.emit()
        QMessageBox.information(self, "Saved", "Settings saved. Restart MAX for provider changes to take effect.")
        self.accept()

    def _clear_memory(self):
        result = QMessageBox.question(
            self, "Clear Memory",
            "Delete all stored conversation history?\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if result == QMessageBox.StandardButton.Yes:
            try:
                from memory.memory_engine import MemoryEngine
                mem = MemoryEngine()
                mem.clear()
                mem.close()
                QMessageBox.information(self, "Done", "Memory cleared.")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not clear memory: {e}")
