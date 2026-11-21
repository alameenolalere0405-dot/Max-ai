"""
MAX AI — First-Launch Onboarding Wizard
LEREON Technologies

Professional 7-step setup wizard for new users.
Steps: Welcome → Provider → API Key → Verify → Permissions → Personalize → Done
"""

import asyncio
import threading
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QCheckBox, QComboBox, QProgressBar, QWidget,
    QStackedWidget, QFrame, QScrollArea, QSlider, QTextEdit
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QColor, QDesktopServices
from PyQt6.QtCore import QUrl


PROVIDERS_INFO = [
    {
        "id": "openai",
        "name": "OpenAI",
        "models": "GPT-4o, o1, o3-mini",
        "url": "https://platform.openai.com/api-keys",
        "note": "Requires a paid account. Fast, capable, widely supported.",
        "env_key": "OPENAI_API_KEY",
    },
    {
        "id": "anthropic",
        "name": "Anthropic Claude",
        "models": "Claude Opus, Sonnet, Haiku",
        "url": "https://console.anthropic.com/settings/keys",
        "note": "Excellent for analysis and long documents. Requires paid account.",
        "env_key": "ANTHROPIC_API_KEY",
    },
    {
        "id": "gemini",
        "name": "Google Gemini",
        "models": "Gemini 1.5 Pro, Flash",
        "url": "https://aistudio.google.com/app/apikey",
        "note": "Free tier available. Good multimodal capabilities.",
        "env_key": "GOOGLE_API_KEY",
    },
    {
        "id": "groq",
        "name": "Groq",
        "models": "Llama 3, Mixtral",
        "url": "https://console.groq.com/keys",
        "note": "Free tier with rate limits. Very fast inference.",
        "env_key": "GROQ_API_KEY",
    },
    {
        "id": "deepseek",
        "name": "DeepSeek",
        "models": "DeepSeek Chat, Coder",
        "url": "https://platform.deepseek.com/api_keys",
        "note": "Cost-effective. Strong coding capabilities.",
        "env_key": "DEEPSEEK_API_KEY",
    },
    {
        "id": "mistral",
        "name": "Mistral AI",
        "models": "Mistral Large, Small",
        "url": "https://console.mistral.ai/api-keys",
        "note": "European provider. Free trial available.",
        "env_key": "MISTRAL_API_KEY",
    },
    {
        "id": "openrouter",
        "name": "OpenRouter",
        "models": "100+ models from all providers",
        "url": "https://openrouter.ai/keys",
        "note": "Gateway to many models. Good for trying different providers.",
        "env_key": "OPENROUTER_API_KEY",
    },
    {
        "id": "ollama",
        "name": "Ollama (Local)",
        "models": "Llama 3, Mistral, Phi, Gemma",
        "url": "https://ollama.com/download",
        "note": "Free, runs locally on your computer. Requires Ollama installed.",
        "env_key": None,
    },
]

STYLE = """
QDialog { background: #020812; color: #D0ECF8; }
QWidget { background: transparent; color: #D0ECF8; font-family: 'Segoe UI', Arial, sans-serif; }
QLabel { background: transparent; }
QPushButton {
    background: #071828; color: #00BFFF; border: 1px solid #0A3A5A;
    border-radius: 6px; padding: 9px 20px; font-size: 13px; font-weight: 500;
}
QPushButton:hover { background: #0A2A45; border-color: #00BFFF; }
QPushButton:pressed { background: #00BFFF; color: #020812; }
QPushButton#primary {
    background: #004A80; color: #D9F8FF; border: 1px solid #00BFFF;
    font-size: 14px; padding: 11px 28px;
}
QPushButton#primary:hover { background: #0070B0; }
QPushButton#skip { background: transparent; color: #2A6080; border: none; }
QPushButton#skip:hover { color: #4090B0; }
QLineEdit {
    background: #040F1E; color: #D0ECF8; border: 1px solid #0A2A45;
    border-radius: 6px; padding: 10px 12px; font-size: 13px;
}
QLineEdit:focus { border-color: #00BFFF; }
QComboBox {
    background: #040F1E; color: #D0ECF8; border: 1px solid #0A2A45;
    border-radius: 6px; padding: 8px 12px; font-size: 13px;
}
QComboBox::drop-down { border: none; width: 24px; }
QComboBox QAbstractItemView {
    background: #040F1E; color: #D0ECF8; border: 1px solid #0A2A45;
    selection-background-color: #004A80;
}
QCheckBox { color: #90C0D8; spacing: 8px; }
QCheckBox::indicator {
    width: 18px; height: 18px; border: 1px solid #0A3A5A;
    border-radius: 4px; background: #040F1E;
}
QCheckBox::indicator:checked { background: #00BFFF; border-color: #00BFFF; }
QProgressBar {
    background: #040F1E; border: 1px solid #0A2A45; border-radius: 4px; height: 8px;
}
QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #004A80,stop:1 #00BFFF); border-radius: 4px; }
QScrollBar:vertical { background: #040F1E; width: 6px; border-radius: 3px; }
QScrollBar::handle:vertical { background: #0A3A5A; border-radius: 3px; min-height: 20px; }
"""


class VerifyWorker(QThread):
    success = pyqtSignal(str)
    failure = pyqtSignal(str)

    def __init__(self, provider_id: str, api_key: str):
        super().__init__()
        self._provider = provider_id
        self._key = api_key

    def run(self):
        import sys, os
        sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent.parent))
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self._test())
            loop.close()
            self.success.emit(result)
        except Exception as e:
            self.failure.emit(str(e))

    async def _test(self) -> str:
        """Send a minimal test message to verify the API key works."""
        import importlib
        providers = {
            "openai":    ("providers.openai_provider",    "OpenAIProvider",    {"api_key": self._key, "model": "gpt-4o-mini"}),
            "anthropic": ("providers.anthropic_provider", "AnthropicProvider", {"api_key": self._key, "model": "claude-haiku-4-5"}),
            "gemini":    ("providers.gemini_provider",    "GeminiProvider",    {"api_key": self._key, "model": "gemini-1.5-flash"}),
            "groq":      ("providers.groq_provider",      "GroqProvider",      {"api_key": self._key, "model": "llama3-8b-8192"}),
            "deepseek":  ("providers.openai_provider",    "OpenAIProvider",    {"api_key": self._key, "model": "deepseek-chat", "base_url": "https://api.deepseek.com/v1", "name": "deepseek"}),
            "mistral":   ("providers.mistral_provider",   "MistralProvider",   {"api_key": self._key, "model": "mistral-small-latest"}),
            "openrouter":("providers.openai_provider",    "OpenAIProvider",    {"api_key": self._key, "model": "openai/gpt-4o-mini", "base_url": "https://openrouter.ai/api/v1", "name": "openrouter"}),
        }
        if self._provider == "ollama":
            import aiohttp
            try:
                async with aiohttp.ClientSession() as s:
                    async with s.get("http://localhost:11434/api/tags", timeout=aiohttp.ClientTimeout(total=5)) as r:
                        if r.status == 200:
                            return "Ollama is running locally."
                        return f"Ollama returned HTTP {r.status}"
            except Exception as e:
                raise ConnectionError(f"Cannot reach Ollama at localhost:11434. Is it running?\n{e}")

        entry = providers.get(self._provider)
        if not entry:
            raise ValueError(f"Unknown provider: {self._provider}")
        mod_name, cls_name, kw = entry
        mod = importlib.import_module(mod_name)
        cls = getattr(mod, cls_name)
        p = cls(**kw)
        text, model, _ = await p.complete(
            messages=[{"role": "user", "content": "Reply with exactly: OK"}],
            system="Reply with exactly the word OK and nothing else.",
            max_tokens=10
        )
        return f"Connected to {self._provider} ({model}). Response: {text.strip()[:30]}"


class OnboardingWizard(QDialog):
    """7-step first-launch setup wizard."""
    completed = pyqtSignal(str, str)   # provider_id, api_key

    STEP_TITLES = [
        "Welcome to MAX AI",
        "Choose Your AI Provider",
        "Configure API Key",
        "Verify Connection",
        "Set Permissions",
        "Personalize MAX",
        "You're All Set!",
    ]

    def __init__(self, config=None, parent=None):
        super().__init__(parent)
        self._config = config
        self._selected_provider = PROVIDERS_INFO[0]
        self._api_key = ""
        self._verify_worker = None

        self.setWindowTitle("MAX AI — Setup Wizard")
        self.setMinimumSize(640, 540)
        self.setModal(True)
        self.setStyleSheet(STYLE)

        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # Progress bar
        self._progress = QProgressBar()
        self._progress.setRange(0, len(self.STEP_TITLES) - 1)
        self._progress.setValue(0)
        self._progress.setTextVisible(False)
        self._progress.setFixedHeight(4)
        layout.addWidget(self._progress)

        # Step indicator
        self._step_lbl = QLabel()
        self._step_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._step_lbl.setStyleSheet("color:#1A5070;font-size:11px;padding:6px;background:#030C18;")
        layout.addWidget(self._step_lbl)

        # Pages
        self._stack = QStackedWidget()
        self._stack.addWidget(self._page_welcome())
        self._stack.addWidget(self._page_provider())
        self._stack.addWidget(self._page_apikey())
        self._stack.addWidget(self._page_verify())
        self._stack.addWidget(self._page_permissions())
        self._stack.addWidget(self._page_personalize())
        self._stack.addWidget(self._page_done())
        layout.addWidget(self._stack, 1)

        # Nav buttons
        nav = QWidget()
        nav.setStyleSheet("background:#030C18;border-top:1px solid #0A2A45;")
        nav_l = QHBoxLayout(nav)
        nav_l.setContentsMargins(20, 12, 20, 12)

        self._back_btn = QPushButton("← Back")
        self._back_btn.clicked.connect(self._back)
        self._back_btn.setVisible(False)

        self._skip_btn = QPushButton("Skip")
        self._skip_btn.setObjectName("skip")
        self._skip_btn.clicked.connect(self._skip)

        self._next_btn = QPushButton("Next →")
        self._next_btn.setObjectName("primary")
        self._next_btn.clicked.connect(self._next)

        nav_l.addWidget(self._back_btn)
        nav_l.addStretch()
        nav_l.addWidget(self._skip_btn)
        nav_l.addWidget(self._next_btn)
        layout.addWidget(nav)

        self._update_nav()

    # ── Pages ─────────────────────────────────────────────────────────────

    def _page_welcome(self) -> QWidget:
        w = QWidget()
        vl = QVBoxLayout(w)
        vl.setContentsMargins(50, 40, 50, 20)
        vl.setSpacing(16)
        vl.addStretch()

        logo = QLabel("✦ MAX AI")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet("color:#00BFFF;font-size:32px;font-weight:bold;letter-spacing:4px;")
        vl.addWidget(logo)

        tagline = QLabel("Modular Autonomous eXecutive")
        tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tagline.setStyleSheet("color:#1A5070;font-size:13px;letter-spacing:1px;")
        vl.addWidget(tagline)

        vl.addSpacing(20)

        desc = QLabel(
            "Welcome to MAX AI — your intelligent personal assistant, developed by LEREON Technologies.\n\n"
            "MAX connects to powerful AI models to help you chat, write, research, automate tasks, "
            "manage files, and more — all from one unified desktop application.\n\n"
            "This wizard will guide you through a quick setup. It takes about 2 minutes."
        )
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("color:#90C0D8;font-size:13px;line-height:1.6;")
        vl.addWidget(desc)

        vl.addSpacing(16)

        note = QLabel("Your API keys and conversations are stored locally on your computer.\nNothing is sent to LEREON Technologies.")
        note.setWordWrap(True)
        note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        note.setStyleSheet("color:#2A6080;font-size:11px;")
        vl.addWidget(note)

        vl.addStretch()
        return w

    def _page_provider(self) -> QWidget:
        w = QWidget()
        vl = QVBoxLayout(w)
        vl.setContentsMargins(40, 30, 40, 10)
        vl.setSpacing(10)

        h = QLabel("Choose Your AI Provider")
        h.setStyleSheet("color:#00BFFF;font-size:18px;font-weight:bold;")
        vl.addWidget(h)

        sub = QLabel("MAX AI works with many AI providers. Choose the one you have an account with.")
        sub.setWordWrap(True)
        sub.setStyleSheet("color:#4090B0;font-size:12px;")
        vl.addWidget(sub)

        vl.addSpacing(8)

        self._prov_combo = QComboBox()
        for p in PROVIDERS_INFO:
            self._prov_combo.addItem(p["name"], p)
        self._prov_combo.currentIndexChanged.connect(self._on_prov_changed)
        vl.addWidget(self._prov_combo)

        self._prov_detail = QLabel()
        self._prov_detail.setWordWrap(True)
        self._prov_detail.setStyleSheet(
            "background:#040F1E;border:1px solid #0A2A45;border-radius:8px;"
            "padding:14px;color:#90C0D8;font-size:12px;line-height:1.5;"
        )
        vl.addWidget(self._prov_detail)

        self._prov_link_btn = QPushButton("🌐  Open Provider Website")
        self._prov_link_btn.setStyleSheet(
            "QPushButton{background:transparent;color:#00BFFF;border:1px solid #0A3A5A;"
            "border-radius:6px;padding:7px 16px;font-size:12px;}"
            "QPushButton:hover{border-color:#00BFFF;background:#071828;}"
        )
        self._prov_link_btn.clicked.connect(self._open_provider_link)
        vl.addWidget(self._prov_link_btn)

        vl.addStretch()
        self._on_prov_changed(0)
        return w

    def _page_apikey(self) -> QWidget:
        w = QWidget()
        vl = QVBoxLayout(w)
        vl.setContentsMargins(40, 30, 40, 10)
        vl.setSpacing(12)

        self._apikey_title = QLabel("Enter Your API Key")
        self._apikey_title.setStyleSheet("color:#00BFFF;font-size:18px;font-weight:bold;")
        vl.addWidget(self._apikey_title)

        self._apikey_desc = QLabel()
        self._apikey_desc.setWordWrap(True)
        self._apikey_desc.setStyleSheet("color:#4090B0;font-size:12px;")
        vl.addWidget(self._apikey_desc)

        what_lbl = QLabel("What is an API key?")
        what_lbl.setStyleSheet("color:#D0ECF8;font-size:12px;font-weight:bold;margin-top:8px;")
        vl.addWidget(what_lbl)

        what_desc = QLabel(
            "An API key is a password that lets MAX AI connect to your AI provider account. "
            "It stays on your computer — MAX AI never sends it to LEREON Technologies."
        )
        what_desc.setWordWrap(True)
        what_desc.setStyleSheet("color:#4090B0;font-size:12px;")
        vl.addWidget(what_desc)

        key_lbl = QLabel("Paste your API key below:")
        key_lbl.setStyleSheet("color:#D0ECF8;font-size:12px;margin-top:8px;")
        vl.addWidget(key_lbl)

        self._key_input = QLineEdit()
        self._key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._key_input.setPlaceholderText("sk-... or similar")
        self._key_input.textChanged.connect(self._on_key_changed)
        vl.addWidget(self._key_input)

        self._show_key_cb = QCheckBox("Show key")
        self._show_key_cb.toggled.connect(
            lambda c: self._key_input.setEchoMode(
                QLineEdit.EchoMode.Normal if c else QLineEdit.EchoMode.Password
            )
        )
        vl.addWidget(self._show_key_cb)

        self._storage_lbl = QLabel()
        self._storage_lbl.setStyleSheet("color:#1A5070;font-size:10px;")
        vl.addWidget(self._storage_lbl)

        # Update storage method label
        try:
            from core.secure_storage import storage_method
            self._storage_lbl.setText(f"🔒 Storage: {storage_method()}")
        except Exception:
            self._storage_lbl.setText("🔒 Stored locally on your device")

        vl.addStretch()
        return w

    def _page_verify(self) -> QWidget:
        w = QWidget()
        vl = QVBoxLayout(w)
        vl.setContentsMargins(40, 30, 40, 10)
        vl.setSpacing(16)

        h = QLabel("Verifying Connection")
        h.setStyleSheet("color:#00BFFF;font-size:18px;font-weight:bold;")
        vl.addWidget(h)

        self._verify_status = QLabel("Testing your API key…")
        self._verify_status.setWordWrap(True)
        self._verify_status.setStyleSheet("color:#90C0D8;font-size:13px;")
        vl.addWidget(self._verify_status)

        self._verify_progress = QProgressBar()
        self._verify_progress.setRange(0, 0)  # Indeterminate
        self._verify_progress.setFixedHeight(8)
        vl.addWidget(self._verify_progress)

        self._verify_result = QLabel()
        self._verify_result.setWordWrap(True)
        self._verify_result.setStyleSheet(
            "background:#040F1E;border:1px solid #0A2A45;border-radius:8px;"
            "padding:14px;font-size:12px;min-height:60px;"
        )
        self._verify_result.setVisible(False)
        vl.addWidget(self._verify_result)

        self._retry_btn = QPushButton("Try Again")
        self._retry_btn.setVisible(False)
        self._retry_btn.clicked.connect(self._start_verify)
        vl.addWidget(self._retry_btn)

        vl.addStretch()
        return w

    def _page_permissions(self) -> QWidget:
        w = QWidget()
        vl = QVBoxLayout(w)
        vl.setContentsMargins(40, 30, 40, 10)
        vl.setSpacing(10)

        h = QLabel("Optional Permissions")
        h.setStyleSheet("color:#00BFFF;font-size:18px;font-weight:bold;")
        vl.addWidget(h)

        sub = QLabel(
            "These features are optional. All are off by default for your privacy. "
            "You can change these any time in Settings."
        )
        sub.setWordWrap(True)
        sub.setStyleSheet("color:#4090B0;font-size:12px;")
        vl.addWidget(sub)

        permissions = [
            ("microphone",     "🎤  Microphone",       "Voice input — speak to MAX instead of typing"),
            ("screen_capture", "📸  Screen Capture",    "MAX can take screenshots to understand your screen"),
            ("file_read",      "📂  File Access",       "MAX can read files you share with it"),
            ("pc_control",     "💻  Desktop Control",   "MAX can open apps and manage files (needs confirmation)"),
            ("memory",         "🧠  Memory",            "MAX remembers your conversations between sessions"),
            ("web_browsing",   "🌐  Web Browsing",      "MAX can search the web and fetch URLs"),
        ]

        self._perm_checks: dict = {}
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        perm_w = QWidget()
        perm_vl = QVBoxLayout(perm_w)
        perm_vl.setSpacing(6)

        # Sensible pre-ticked defaults
        defaults_on = {"memory", "web_browsing", "file_read"}
        for key, label, desc in permissions:
            row = QWidget()
            row_l = QHBoxLayout(row)
            row_l.setContentsMargins(12, 8, 12, 8)
            row.setStyleSheet("background:#040F1E;border:1px solid #0A2A45;border-radius:8px;")

            cb = QCheckBox(label)
            cb.setChecked(key in defaults_on)
            cb.setStyleSheet("color:#D0ECF8;font-size:13px;font-weight:bold;")
            self._perm_checks[key] = cb

            desc_lbl = QLabel(desc)
            desc_lbl.setStyleSheet("color:#4090B0;font-size:11px;")

            info_vl = QVBoxLayout()
            info_vl.addWidget(cb)
            info_vl.addWidget(desc_lbl)
            info_vl.setSpacing(2)
            row_l.addLayout(info_vl)
            perm_vl.addWidget(row)

        scroll.setWidget(perm_w)
        vl.addWidget(scroll, 1)
        return w

    def _page_personalize(self) -> QWidget:
        w = QWidget()
        vl = QVBoxLayout(w)
        vl.setContentsMargins(40, 30, 40, 10)
        vl.setSpacing(12)

        h = QLabel("Personalize MAX")
        h.setStyleSheet("color:#00BFFF;font-size:18px;font-weight:bold;")
        vl.addWidget(h)

        sub = QLabel("Customize how MAX looks and behaves. You can change these anytime in Settings.")
        sub.setWordWrap(True)
        sub.setStyleSheet("color:#4090B0;font-size:12px;")
        vl.addWidget(sub)

        # Assistant name
        name_lbl = QLabel("Assistant Name:")
        name_lbl.setStyleSheet("color:#D0ECF8;font-size:12px;margin-top:8px;")
        vl.addWidget(name_lbl)
        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("MAX")
        self._name_input.setText("MAX")
        vl.addWidget(self._name_input)

        # Personality mode
        mode_lbl = QLabel("Personality Mode:")
        mode_lbl.setStyleSheet("color:#D0ECF8;font-size:12px;margin-top:4px;")
        vl.addWidget(mode_lbl)
        self._mode_combo = QComboBox()
        for m in ["Sarcastic (default)", "Professional", "Friendly", "Nerdy", "Creative", "Savage"]:
            self._mode_combo.addItem(m)
        vl.addWidget(self._mode_combo)

        # Theme
        theme_lbl = QLabel("Theme:")
        theme_lbl.setStyleSheet("color:#D0ECF8;font-size:12px;margin-top:4px;")
        vl.addWidget(theme_lbl)
        self._theme_combo = QComboBox()
        for t in ["Dark (default)", "Dark Blue", "Dark Purple"]:
            self._theme_combo.addItem(t)
        vl.addWidget(self._theme_combo)

        vl.addStretch()
        return w

    def _page_done(self) -> QWidget:
        w = QWidget()
        vl = QVBoxLayout(w)
        vl.setContentsMargins(50, 40, 50, 20)
        vl.setSpacing(16)
        vl.addStretch()

        check = QLabel("✓")
        check.setAlignment(Qt.AlignmentFlag.AlignCenter)
        check.setStyleSheet("color:#00FF88;font-size:64px;")
        vl.addWidget(check)

        h = QLabel("MAX AI is ready.")
        h.setAlignment(Qt.AlignmentFlag.AlignCenter)
        h.setStyleSheet("color:#00BFFF;font-size:24px;font-weight:bold;")
        vl.addWidget(h)

        sub = QLabel(
            "Your AI provider is configured and ready to use.\n\n"
            "Start a conversation by typing in the chat below, or use the microphone button "
            "if you enabled voice input.\n\n"
            "You can always adjust settings from the sidebar."
        )
        sub.setWordWrap(True)
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet("color:#4090B0;font-size:13px;line-height:1.6;")
        vl.addWidget(sub)

        footer = QLabel("MAX AI © 2026 LEREON Technologies. All rights reserved.")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet("color:#1A4060;font-size:10px;")
        vl.addWidget(footer)

        vl.addStretch()
        return w

    # ── Navigation ────────────────────────────────────────────────────────

    def _current_step(self) -> int:
        return self._stack.currentIndex()

    def _next(self):
        step = self._current_step()
        if step == 0:  # Welcome → Provider
            self._go(1)
        elif step == 1:  # Provider → API Key
            self._update_apikey_page()
            self._go(2)
        elif step == 2:  # API Key → Verify
            self._api_key = self._key_input.text().strip()
            if not self._api_key and self._selected_provider["id"] != "ollama":
                self._key_input.setStyleSheet(
                    "background:#040F1E;border:1px solid #FF4455;border-radius:6px;padding:10px 12px;"
                )
                return
            self._go(3)
            self._start_verify()
        elif step == 3:  # Verify → Permissions
            self._go(4)
        elif step == 4:  # Permissions → Personalize
            self._apply_permissions()
            self._go(5)
        elif step == 5:  # Personalize → Done
            self._apply_personalization()
            self._go(6)
        elif step == 6:  # Done → Close
            self._finish()

    def _back(self):
        self._go(max(0, self._current_step() - 1))

    def _skip(self):
        step = self._current_step()
        if step in (2, 3):  # Skip API key / verify
            self._go(4)
        elif step == 4:
            self._go(5)
        elif step == 5:
            self._go(6)
        else:
            self._next()

    def _go(self, step: int):
        self._stack.setCurrentIndex(step)
        self._progress.setValue(step)
        self._step_lbl.setText(
            f"Step {step + 1} of {len(self.STEP_TITLES)} — {self.STEP_TITLES[step]}"
        )
        self._update_nav()

    def _update_nav(self):
        step = self._current_step()
        self._back_btn.setVisible(step > 0)
        is_last = step == len(self.STEP_TITLES) - 1
        self._next_btn.setText("Start MAX AI →" if is_last else "Next →")
        self._skip_btn.setVisible(step in (2, 3, 4, 5))

    # ── Provider selection ────────────────────────────────────────────────

    def _on_prov_changed(self, idx: int):
        p = self._prov_combo.itemData(idx)
        if p:
            self._selected_provider = p
            self._prov_detail.setText(
                f"<b style='color:#00BFFF'>{p['name']}</b><br>"
                f"<span style='color:#4090B0'>Models:</span> {p['models']}<br><br>"
                f"{p['note']}"
            )

    def _open_provider_link(self):
        url = self._selected_provider.get("url", "")
        if url:
            QDesktopServices.openUrl(QUrl(url))

    def _update_apikey_page(self):
        p = self._selected_provider
        self._apikey_title.setText(f"Enter Your {p['name']} API Key")
        if p["id"] == "ollama":
            self._apikey_desc.setText(
                "Ollama runs AI models locally on your computer — no API key required.\n"
                f"You need to install Ollama first: {p['url']}\n\n"
                "After installing, run: ollama serve"
            )
            self._key_input.setEnabled(False)
            self._key_input.setPlaceholderText("No API key needed for Ollama")
        else:
            self._key_input.setEnabled(True)
            self._key_input.setPlaceholderText("Paste your API key here…")
            self._apikey_desc.setText(
                f"Get your {p['name']} API key from:\n{p['url']}\n\n"
                "Your key starts with a unique prefix (e.g. sk-...). "
                "It will be stored securely on your computer."
            )

    def _on_key_changed(self):
        self._key_input.setStyleSheet("")

    # ── Verification ──────────────────────────────────────────────────────

    def _start_verify(self):
        self._verify_result.setVisible(False)
        self._retry_btn.setVisible(False)
        self._verify_progress.setRange(0, 0)
        self._verify_status.setText(f"Testing connection to {self._selected_provider['name']}…")
        self._next_btn.setEnabled(False)

        self._verify_worker = VerifyWorker(self._selected_provider["id"], self._api_key)
        self._verify_worker.success.connect(self._on_verify_success)
        self._verify_worker.failure.connect(self._on_verify_failure)
        self._verify_worker.start()

    def _on_verify_success(self, msg: str):
        self._verify_progress.setRange(0, 1)
        self._verify_progress.setValue(1)
        self._verify_status.setText("✓  Connection successful!")
        self._verify_status.setStyleSheet("color:#00FF88;font-size:13px;")
        self._verify_result.setText(msg)
        self._verify_result.setStyleSheet(
            "background:#020F08;border:1px solid #00AA44;border-radius:8px;"
            "padding:14px;color:#00FF88;font-size:12px;"
        )
        self._verify_result.setVisible(True)
        self._next_btn.setEnabled(True)

    def _on_verify_failure(self, err: str):
        self._verify_progress.setRange(0, 1)
        self._verify_progress.setValue(0)
        self._verify_status.setText("✗  Connection failed")
        self._verify_status.setStyleSheet("color:#FF4455;font-size:13px;")
        # Never show the actual key in error messages
        safe_err = err.replace(self._api_key, "***") if self._api_key else err
        self._verify_result.setText(
            f"Error: {safe_err}\n\n"
            "Check that your API key is correct and your account has credits."
        )
        self._verify_result.setStyleSheet(
            "background:#0F0208;border:1px solid #AA2244;border-radius:8px;"
            "padding:14px;color:#FF8899;font-size:12px;"
        )
        self._verify_result.setVisible(True)
        self._retry_btn.setVisible(True)
        self._next_btn.setEnabled(True)  # Allow skipping forward

    # ── Apply settings ────────────────────────────────────────────────────

    def _apply_permissions(self):
        if not self._config:
            return
        for key, cb in self._perm_checks.items():
            self._config.set("permissions", key, cb.isChecked())
        self._config.save()

    def _apply_personalization(self):
        if not self._config:
            return
        name = self._name_input.text().strip() or "MAX"
        self._config.set("assistant", "name", name)

        mode_map = {
            0: "sarcastic", 1: "professional", 2: "friendly",
            3: "nerdy", 4: "creative", 5: "savage"
        }
        self._config.set("personality", "mode", mode_map.get(self._mode_combo.currentIndex(), "sarcastic"))
        self._config.save()

    def _finish(self):
        """Save API key and mark setup complete."""
        if self._api_key and self._selected_provider["id"] != "ollama":
            try:
                from core.secure_storage import set_provider_key
                set_provider_key(self._selected_provider["id"], self._api_key)
            except Exception as e:
                import logging
                logging.getLogger("MAX.onboarding").warning(f"Key save error: {e}")

        if self._config:
            pid = self._selected_provider["id"]
            self._config.set("providers", pid, "enabled", True)
            self._config.set("providers", "default", pid)
            self._config.set("app", "setup_complete", True)
            self._config.save()

        self.completed.emit(
            self._selected_provider["id"],
            self._api_key
        )
        self.accept()


def should_show_wizard(config) -> bool:
    """Return True if first-launch wizard should be shown."""
    return not config.get("app", "setup_complete", default=False)
