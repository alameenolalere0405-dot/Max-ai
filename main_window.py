"""
MAX AI — Main Window (HUD Edition)
LEREON Technologies

Layout: Slim sidebar | Full chat workspace with sphere header
Hidden panels accessible via tab strip at top-right.
Clean, futuristic, not crowded.
"""

import sys
import time
import threading
import uuid
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QPushButton, QFrame, QSizePolicy, QStatusBar,
    QComboBox, QListWidget, QListWidgetItem, QMessageBox,
    QTabWidget, QStackedWidget, QTextEdit, QLineEdit,
    QFileDialog, QProgressBar, QSlider, QCheckBox,
    QScrollArea, QSplitter, QApplication
)
from PyQt6.QtCore import Qt, QTimer, QSize, pyqtSignal, QThread, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor, QAction, QPalette, QIcon

from core.max_core import MAXState
from ui.core_widget import CoreWidget
from ui.chat_widget import ChatWidget


# ── Helpers ───────────────────────────────────────────────────────────────

def _sep():
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setStyleSheet("color: #0A2A45; margin: 2px 0;")
    return f


def _vsep():
    f = QFrame()
    f.setFrameShape(QFrame.Shape.VLine)
    f.setStyleSheet("color: #0A2A45;")
    return f


def _pill(text, color="#00BFFF", bg="#040F1E"):
    lbl = QLabel(text)
    lbl.setStyleSheet(
        f"color:{color}; background:{bg}; border:1px solid {color}22;"
        "border-radius:10px; padding:2px 10px; font-size:10px; font-weight:bold;"
    )
    return lbl


def _card(title: str = ""):
    """Returns (widget, inner_layout)"""
    outer = QWidget()
    outer.setStyleSheet(
        "background:#041020; border:1px solid #0A2A45; border-radius:10px;"
    )
    vl = QVBoxLayout(outer)
    vl.setSpacing(0)
    vl.setContentsMargins(0, 0, 0, 0)
    if title:
        hdr = QLabel(f"  {title.upper()}")
        hdr.setStyleSheet(
            "color:#00BFFF; font-size:10px; font-weight:bold; letter-spacing:1px;"
            "padding:8px 12px 6px; border-bottom:1px solid #0A2A45; background:transparent;"
        )
        vl.addWidget(hdr)
    inner = QVBoxLayout()
    inner.setSpacing(6)
    inner.setContentsMargins(10, 8, 10, 10)
    vl.addLayout(inner)
    return outer, inner


class NavButton(QPushButton):
    def __init__(self, icon: str, label: str, parent=None):
        super().__init__(parent)
        self.setText(f"{icon}")
        self.setToolTip(label)
        self.setFixedSize(44, 44)
        self.setStyleSheet("""
            QPushButton {
                background: transparent; border: none;
                color: #2A6080; font-size: 20px; border-radius: 8px;
            }
            QPushButton:hover { background: #071828; color: #00E5FF; }
            QPushButton:checked { background: #0A2A45; color: #00E5FF;
                border-left: 2px solid #00E5FF; border-radius: 0px 8px 8px 0px; }
        """)
        self.setCheckable(True)


# ── Main Window ───────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self, force_provider=None, start_voice=False, debug=False):
        super().__init__()
        self._force_provider = force_provider
        self._start_voice = start_voice
        self._debug = debug
        self._voice_active = False
        self._activity: list = []
        self._current_conv_id = ""

        # Boot core
        from core.max_core import MAXCore
        self._core = MAXCore()
        self._core.on_state_change(self._on_state_change)

        self.setWindowTitle("MAX AI — LEREON Technologies")
        self.setMinimumSize(1000, 660)
        self.resize(1280, 820)

        self._build_ui()
        self._build_menu()

        # Timers
        QTimer.singleShot(0, self._update_clock)
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start(1000)

        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._refresh_status)
        self._refresh_timer.start(3000)

        # Monitor
        self._core.monitor.on_update(lambda s: QTimer.singleShot(0, lambda snap=s: self._on_monitor(snap)))

        # Start new conversation
        self._new_conversation()

        if start_voice:
            QTimer.singleShot(600, self._toggle_voice)

        # Check onboarding
        from ui.onboarding import should_show_wizard
        if should_show_wizard(self._core.config):
            QTimer.singleShot(200, self._show_onboarding)

    # ── UI BUILD ──────────────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        ml = QHBoxLayout(central)
        ml.setSpacing(0)
        ml.setContentsMargins(0, 0, 0, 0)

        # 1. Icon nav rail (slim, 56px)
        ml.addWidget(self._build_nav_rail())

        # 2. Main content stack
        self._content_stack = QStackedWidget()
        self._content_stack.addWidget(self._build_chat_view())      # 0 - chat
        self._content_stack.addWidget(self._build_tools_view())     # 1 - tools
        self._content_stack.addWidget(self._build_memory_view())    # 2 - memory
        self._content_stack.addWidget(self._build_settings_view())  # 3 - settings
        ml.addWidget(self._content_stack, 1)

    def _build_nav_rail(self) -> QWidget:
        """Ultra-slim icon navigation rail."""
        rail = QWidget()
        rail.setFixedWidth(56)
        rail.setStyleSheet("background:#020E1C; border-right:1px solid #0A2A45;")
        vl = QVBoxLayout(rail)
        vl.setSpacing(4)
        vl.setContentsMargins(6, 8, 6, 8)
        vl.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Logo mark
        logo = QLabel("✦")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet("color:#00E5FF; font-size:22px; padding:8px 0;")
        vl.addWidget(logo)
        vl.addWidget(_sep())
        vl.addSpacing(4)

        self._nav_btns = {}
        nav_items = [
            ("chat",     "💬", "Chat"),
            ("tools",    "🛠", "Tools & Studio"),
            ("memory",   "🧠", "Memory & Knowledge"),
            ("settings", "⚙", "Settings"),
        ]
        for key, icon, label in nav_items:
            btn = NavButton(icon, label)
            btn.clicked.connect(lambda checked, k=key: self._nav_to(k))
            vl.addWidget(btn)
            self._nav_btns[key] = btn

        self._nav_btns["chat"].setChecked(True)
        vl.addStretch()

        # Bottom: voice + clock
        self._nav_mic = QPushButton("🎤")
        self._nav_mic.setToolTip("Voice input")
        self._nav_mic.setFixedSize(40, 40)
        self._nav_mic.setStyleSheet(
            "QPushButton{background:#041020;border:1px solid #0A2A45;border-radius:20px;"
            "color:#2A6080;font-size:17px;}"
            "QPushButton:hover{border-color:#00E5FF;color:#00E5FF;}"
            "QPushButton:checked{background:#004A30;border-color:#00FF88;color:#00FF88;}"
        )
        self._nav_mic.setCheckable(True)
        self._nav_mic.clicked.connect(self._toggle_voice)
        vl.addWidget(self._nav_mic)

        self._nav_clock = QLabel()
        self._nav_clock.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._nav_clock.setStyleSheet("color:#1A4060;font-size:9px;")
        vl.addWidget(self._nav_clock)

        return rail

    def _nav_to(self, key: str):
        idx = {"chat": 0, "tools": 1, "memory": 2, "settings": 3}
        for k, btn in self._nav_btns.items():
            btn.setChecked(k == key)
        self._content_stack.setCurrentIndex(idx.get(key, 0))

    # ── CHAT VIEW ─────────────────────────────────────────────────────────

    def _build_chat_view(self) -> QWidget:
        """Main chat view: left panel (sphere+history) | right chat."""
        w = QWidget()
        hl = QHBoxLayout(w)
        hl.setSpacing(0)
        hl.setContentsMargins(0, 0, 0, 0)

        # Left panel: sphere + conversation list (collapsible)
        left = QWidget()
        left.setFixedWidth(220)
        left.setStyleSheet("background:#020E1C; border-right:1px solid #0A2A45;")
        left_vl = QVBoxLayout(left)
        left_vl.setSpacing(0)
        left_vl.setContentsMargins(0, 0, 0, 0)

        # Sphere
        sphere_area = QWidget()
        sphere_area.setFixedHeight(210)
        sphere_area.setStyleSheet("background:#020812;")
        sl = QVBoxLayout(sphere_area)
        sl.setContentsMargins(0, 10, 0, 6)

        self._core_widget = CoreWidget()
        self._core_widget.setFixedSize(190, 170)
        sphere_row_w = QWidget()
        sphere_row_l = QHBoxLayout(sphere_row_w)
        sphere_row_l.addStretch()
        sphere_row_l.addWidget(self._core_widget)
        sphere_row_l.addStretch()
        sl.addWidget(sphere_row_w)

        self._state_lbl = QLabel("IDLE / READY")
        self._state_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._state_lbl.setStyleSheet("color:#1A5070;font-size:9px;letter-spacing:2px;")
        sl.addWidget(self._state_lbl)

        left_vl.addWidget(sphere_area)
        left_vl.addWidget(_sep())

        # New chat + search
        nc_btn = QPushButton("✚  New Chat")
        nc_btn.setObjectName("primary")
        nc_btn.setFixedHeight(34)
        nc_btn.clicked.connect(self._new_conversation)
        nc_w = QWidget()
        nc_l = QVBoxLayout(nc_w)
        nc_l.setContentsMargins(8, 8, 8, 4)
        nc_l.addWidget(nc_btn)
        left_vl.addWidget(nc_w)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Search…")
        self._search_input.setFixedHeight(30)
        self._search_input.textChanged.connect(self._search_convs)
        sw = QWidget()
        sl2 = QVBoxLayout(sw)
        sl2.setContentsMargins(8, 0, 8, 4)
        sl2.addWidget(self._search_input)
        left_vl.addWidget(sw)

        # Conversation list
        sec = QLabel("  CONVERSATIONS")
        sec.setStyleSheet("color:#0A3050;font-size:9px;letter-spacing:1px;padding:4px 8px 2px;")
        left_vl.addWidget(sec)

        self._conv_list = QListWidget()
        self._conv_list.setStyleSheet("""
            QListWidget { background:transparent; border:none; padding:0 4px; }
            QListWidget::item { padding:8px 8px; border-radius:6px; color:#4A90B0;
                                font-size:11px; margin:1px 0; }
            QListWidget::item:selected { background:#0A2A45; color:#D0ECF8; }
            QListWidget::item:hover { background:#071828; color:#D0ECF8; }
        """)
        self._conv_list.currentItemChanged.connect(self._on_conv_selected)
        left_vl.addWidget(self._conv_list, 1)

        # Provider pill
        prov_w = QWidget()
        prov_l = QHBoxLayout(prov_w)
        prov_l.setContentsMargins(8, 4, 8, 8)
        self._prov_combo = QComboBox()
        self._prov_combo.setFixedHeight(28)
        self._prov_combo.setStyleSheet(
            "font-size:11px; background:#030C18; border:1px solid #0A2A45; border-radius:6px; padding:2px 8px;"
        )
        self._refresh_providers()
        self._prov_combo.currentIndexChanged.connect(self._on_provider_changed)
        prov_l.addWidget(QLabel("Provider:"))
        prov_l.addWidget(self._prov_combo, 1)
        left_vl.addWidget(prov_w)

        hl.addWidget(left)

        # Right: chat
        right = QWidget()
        right_vl = QVBoxLayout(right)
        right_vl.setSpacing(0)
        right_vl.setContentsMargins(0, 0, 0, 0)

        # Chat header bar
        right_vl.addWidget(self._build_chat_header())
        right_vl.addWidget(_sep())

        # Chat widget
        self._chat = ChatWidget(self._core)
        right_vl.addWidget(self._chat, 1)
        hl.addWidget(right, 1)

        return w

    def _build_chat_header(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(44)
        bar.setStyleSheet("background:#020E1C;")
        hl = QHBoxLayout(bar)
        hl.setContentsMargins(14, 0, 14, 0)
        hl.setSpacing(10)

        self._conv_title_lbl = QLabel("New Conversation")
        self._conv_title_lbl.setStyleSheet("color:#D0ECF8;font-size:13px;font-weight:bold;")
        hl.addWidget(self._conv_title_lbl)
        hl.addStretch()

        # Status pills
        self._pill_ai  = _pill("● AI", "#00FF88")
        self._pill_prov = _pill("—", "#00BFFF")
        hl.addWidget(self._pill_ai)
        hl.addWidget(self._pill_prov)

        # Collaborate button
        collab = QPushButton("🤝  Collaborate")
        collab.setObjectName("ghost")
        collab.clicked.connect(self._open_collaborate)
        hl.addWidget(collab)

        # Clear chat
        clr = QPushButton("🗑")
        clr.setObjectName("icon_btn")
        clr.setToolTip("Clear conversation")
        clr.clicked.connect(self._clear_chat)
        hl.addWidget(clr)

        # Settings shortcut
        cfg_btn = QPushButton("⚙")
        cfg_btn.setObjectName("icon_btn")
        cfg_btn.setToolTip("Settings")
        cfg_btn.clicked.connect(lambda: self._nav_to("settings"))
        hl.addWidget(cfg_btn)

        self._clock = QLabel()
        self._clock.setStyleSheet("color:#1A4060;font-size:11px;min-width:90px;text-align:right;")
        hl.addWidget(self._clock)

        return bar

    # ── TOOLS VIEW ────────────────────────────────────────────────────────

    def _build_tools_view(self) -> QWidget:
        w = QWidget()
        vl = QVBoxLayout(w)
        vl.setSpacing(0)
        vl.setContentsMargins(0, 0, 0, 0)

        # Header
        hdr = self._view_header("🛠  Tools & Studio", "Studio, Automation, Monitor, Plugins")
        vl.addWidget(hdr)

        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane{border:none;} QTabBar::tab{padding:8px 18px;}")

        tabs.addTab(self._build_studio_tab(), "✍  Studio")
        tabs.addTab(self._build_automation_tab(), "⚡  Automate")
        tabs.addTab(self._build_monitor_tab(), "📊  Monitor")
        tabs.addTab(self._build_plugins_tab(), "🔌  Plugins")
        tabs.addTab(self._build_desktop_tab(), "💻  Desktop")

        vl.addWidget(tabs, 1)
        return w

    def _build_studio_tab(self) -> QWidget:
        w = QWidget()
        vl = QVBoxLayout(w)
        vl.setContentsMargins(16, 12, 16, 12)
        vl.setSpacing(10)

        row = QHBoxLayout()
        task_combo = QComboBox()
        from studio.studio_engine import StudioEngine
        for t in StudioEngine(core=None).task_types:
            task_combo.addItem(t.replace("_", " ").title(), t)
        self._studio_task = task_combo
        row.addWidget(QLabel("Task:"))
        row.addWidget(task_combo, 1)

        load_btn = QPushButton("📂  Load File")
        load_btn.clicked.connect(self._studio_load)
        run_btn = QPushButton("▶  Run")
        run_btn.setObjectName("primary")
        run_btn.clicked.connect(self._studio_run)
        save_btn = QPushButton("💾  Save")
        save_btn.clicked.connect(self._studio_save)
        row.addWidget(load_btn)
        row.addWidget(run_btn)
        row.addWidget(save_btn)
        vl.addLayout(row)

        self._studio_input = QTextEdit()
        self._studio_input.setPlaceholderText(
            "Paste text, code or describe what you need…\n\n"
            "Examples:\n• Summarize this document: [paste text]\n"
            "• Write a README for my Python project\n• Review this code for bugs"
        )
        vl.addWidget(self._studio_input, 1)

        out_lbl = QLabel("Output:")
        out_lbl.setStyleSheet("color:#4A90B0;font-size:11px;")
        vl.addWidget(out_lbl)
        self._studio_output = QTextEdit()
        self._studio_output.setReadOnly(True)
        self._studio_output.setMaximumHeight(200)
        vl.addWidget(self._studio_output)
        return w

    def _build_automation_tab(self) -> QWidget:
        w = QWidget()
        vl = QVBoxLayout(w)
        vl.setContentsMargins(16, 12, 16, 12)
        vl.setSpacing(8)

        btn_row = QHBoxLayout()
        for label, fn in [("➕  New", self._wf_new), ("▶  Run", self._wf_run), ("🗑  Delete", self._wf_delete)]:
            b = QPushButton(label)
            b.clicked.connect(fn)
            btn_row.addWidget(b)
        btn_row.addStretch()
        vl.addLayout(btn_row)

        self._wf_list = QListWidget()
        vl.addWidget(self._wf_list, 1)
        self._wf_status = QLabel("")
        self._wf_status.setStyleSheet("color:#4A90B0;font-size:11px;")
        vl.addWidget(self._wf_status)
        self._refresh_workflows()
        return w

    def _build_monitor_tab(self) -> QWidget:
        w = QWidget()
        vl = QVBoxLayout(w)
        vl.setContentsMargins(16, 12, 16, 12)
        vl.setSpacing(10)

        def _stat(label):
            row = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setFixedWidth(60)
            lbl.setStyleSheet("color:#4A90B0;font-size:11px;")
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setFixedHeight(12)
            val = QLabel("—")
            val.setFixedWidth(44)
            val.setStyleSheet("color:#D0ECF8;font-size:11px;")
            row.addWidget(lbl); row.addWidget(bar, 1); row.addWidget(val)
            rw = QWidget()
            rw.setLayout(row)
            return rw, bar, val

        rw, self._cpu_bar, self._cpu_val = _stat("CPU")
        vl.addWidget(rw)
        rw, self._ram_bar, self._ram_val = _stat("RAM")
        vl.addWidget(rw)
        rw, self._dsk_bar, self._dsk_val = _stat("Disk")
        vl.addWidget(rw)
        rw, self._bat_bar, self._bat_val = _stat("Battery")
        vl.addWidget(rw)

        self._mon_text = QTextEdit()
        self._mon_text.setReadOnly(True)
        self._mon_text.setStyleSheet(
            "font-family:monospace;font-size:11px;background:#020812;border:1px solid #0A2A45;"
            "border-radius:6px;padding:6px;"
        )
        vl.addWidget(self._mon_text, 1)
        return w

    def _build_plugins_tab(self) -> QWidget:
        w = QWidget()
        vl = QVBoxLayout(w)
        vl.setContentsMargins(16, 12, 16, 12)
        vl.setSpacing(8)

        btn_row = QHBoxLayout()
        load_btn = QPushButton("▶  Load Plugin")
        load_btn.clicked.connect(self._plugin_load)
        refresh_btn = QPushButton("🔄  Refresh")
        refresh_btn.clicked.connect(self._plugin_refresh)
        btn_row.addWidget(load_btn)
        btn_row.addWidget(refresh_btn)
        btn_row.addStretch()
        vl.addLayout(btn_row)

        note = QLabel("Drop .py plugin files into plugins/installed/ then click Refresh.")
        note.setStyleSheet("color:#1A5070;font-size:11px;")
        vl.addWidget(note)

        self._plugin_list = QListWidget()
        vl.addWidget(self._plugin_list, 1)
        self._plugin_refresh()
        return w

    def _build_desktop_tab(self) -> QWidget:
        w = QWidget()
        vl = QVBoxLayout(w)
        vl.setContentsMargins(16, 12, 16, 12)
        vl.setSpacing(10)

        note = QLabel(
            "Desktop control lets MAX open apps, manage files, and automate tasks.\n"
            "PC Control permission must be enabled in Settings. All sensitive actions ask for confirmation."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color:#4A90B0;font-size:12px;background:#041020;"
                           "border:1px solid #0A2A45;border-radius:8px;padding:10px;")
        vl.addWidget(note)

        grid = QHBoxLayout()
        for icon, label in [("🌐","Browser"), ("📝","Notes"), ("💻","Terminal"),
                             ("📁","Files"), ("🧮","Calculator"), ("📸","Screenshot")]:
            btn = QPushButton(f"{icon}\n{label}")
            btn.setFixedSize(90, 70)
            btn.setStyleSheet(
                "QPushButton{background:#041020;border:1px solid #0A2A45;border-radius:8px;"
                "color:#4A90B0;font-size:11px;}"
                "QPushButton:hover{border-color:#00E5FF;color:#00E5FF;background:#071828;}"
            )
            app_name = label.lower()
            btn.clicked.connect(lambda checked=False, a=app_name: self._chat.inject_message(f"Open {a}"))
            grid.addWidget(btn)
        grid.addStretch()
        vl.addLayout(grid)
        vl.addStretch()
        return w

    # ── MEMORY VIEW ───────────────────────────────────────────────────────

    def _build_memory_view(self) -> QWidget:
        w = QWidget()
        vl = QVBoxLayout(w)
        vl.setSpacing(0)
        vl.setContentsMargins(0, 0, 0, 0)

        hdr = self._view_header("🧠  Memory & Knowledge", "Conversation history, facts, documents")
        vl.addWidget(hdr)

        tabs = QTabWidget()
        tabs.addTab(self._build_history_tab(), "📜  History")
        tabs.addTab(self._build_knowledge_tab(), "📚  Knowledge Base")
        tabs.addTab(self._build_productivity_tab(), "✅  Productivity")
        vl.addWidget(tabs, 1)
        return w

    def _build_history_tab(self) -> QWidget:
        w = QWidget()
        vl = QVBoxLayout(w)
        vl.setContentsMargins(16, 12, 16, 12)
        vl.setSpacing(8)

        btn_row = QHBoxLayout()
        clr_btn = QPushButton("🗑  Clear Memory")
        clr_btn.setObjectName("danger")
        clr_btn.clicked.connect(self._clear_memory)
        btn_row.addWidget(clr_btn)
        btn_row.addStretch()
        vl.addLayout(btn_row)

        self._history_view = QTextEdit()
        self._history_view.setReadOnly(True)
        self._history_view.setStyleSheet(
            "font-size:12px;background:#020812;border:1px solid #0A2A45;"
            "border-radius:6px;padding:8px;"
        )
        vl.addWidget(self._history_view, 1)
        self._refresh_history()
        return w

    def _build_knowledge_tab(self) -> QWidget:
        w = QWidget()
        vl = QVBoxLayout(w)
        vl.setContentsMargins(16, 12, 16, 12)
        vl.setSpacing(8)

        btn_row = QHBoxLayout()
        import_btn = QPushButton("📂  Import Document")
        import_btn.clicked.connect(self._kb_import)
        search_input = QLineEdit()
        search_input.setPlaceholderText("Search documents…")
        search_input.setFixedHeight(30)
        search_input.returnPressed.connect(lambda: self._kb_search(search_input.text()))
        self._kb_search_input = search_input
        btn_row.addWidget(import_btn)
        btn_row.addWidget(search_input, 1)
        vl.addLayout(btn_row)

        self._kb_list = QListWidget()
        self._kb_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._kb_list.customContextMenuRequested.connect(self._kb_menu)
        vl.addWidget(self._kb_list, 1)
        self._kb_status = QLabel("")
        self._kb_status.setStyleSheet("color:#1A5070;font-size:11px;")
        vl.addWidget(self._kb_status)
        self._refresh_kb()
        return w

    def _build_productivity_tab(self) -> QWidget:
        w = QWidget()
        vl = QVBoxLayout(w)
        vl.setContentsMargins(16, 12, 16, 12)
        vl.setSpacing(8)

        sub_tabs = QTabWidget()
        sub_tabs.setStyleSheet("QTabBar::tab{padding:6px 14px;}")

        # Todos
        td_w = QWidget()
        td_vl = QVBoxLayout(td_w)
        td_vl.setContentsMargins(8, 8, 8, 8)
        td_row = QHBoxLayout()
        self._todo_input = QLineEdit()
        self._todo_input.setPlaceholderText("New task…")
        td_row.addWidget(self._todo_input, 1)
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self._add_todo)
        td_row.addWidget(add_btn)
        td_vl.addLayout(td_row)
        self._todo_list = QListWidget()
        self._todo_list.itemDoubleClicked.connect(self._complete_todo)
        td_vl.addWidget(self._todo_list, 1)
        td_vl.addWidget(QLabel("Double-click to complete", styleSheet="color:#1A5070;font-size:10px;"))
        sub_tabs.addTab(td_w, "✅ Todos")

        # Notes
        nt_w = QWidget()
        nt_vl = QVBoxLayout(nt_w)
        nt_vl.setContentsMargins(8, 8, 8, 8)
        nt_row = QHBoxLayout()
        self._note_title = QLineEdit()
        self._note_title.setPlaceholderText("Note title…")
        nt_row.addWidget(self._note_title, 1)
        note_add = QPushButton("Save")
        note_add.clicked.connect(self._add_note)
        nt_row.addWidget(note_add)
        nt_vl.addLayout(nt_row)
        self._note_body = QTextEdit()
        self._note_body.setPlaceholderText("Note content…")
        nt_vl.addWidget(self._note_body, 1)
        self._notes_list = QListWidget()
        self._notes_list.setMaximumHeight(130)
        nt_vl.addWidget(self._notes_list)
        sub_tabs.addTab(nt_w, "🗒 Notes")

        vl.addWidget(sub_tabs, 1)
        self._refresh_productivity()
        return w

    # ── SETTINGS VIEW ─────────────────────────────────────────────────────

    def _build_settings_view(self) -> QWidget:
        w = QWidget()
        vl = QVBoxLayout(w)
        vl.setSpacing(0)
        vl.setContentsMargins(0, 0, 0, 0)
        hdr = self._view_header("⚙  Settings", "AI providers, permissions, voice, appearance")
        vl.addWidget(hdr)

        from ui.settings_dialog import SettingsDialog
        # Embed settings as inline widget instead of dialog
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        inner = QWidget()
        ivl = QVBoxLayout(inner)
        ivl.setContentsMargins(20, 16, 20, 20)
        ivl.setSpacing(16)

        # Quick API key section
        api_card, api_l = _card("API Keys & Providers")
        note = QLabel("Add API keys to .env file or use the full settings dialog below.")
        note.setStyleSheet("color:#4A90B0;font-size:11px;")
        api_l.addWidget(note)
        open_full = QPushButton("Open Full Settings Dialog")
        open_full.setObjectName("primary")
        open_full.clicked.connect(self._open_full_settings)
        api_l.addWidget(open_full)
        ivl.addWidget(api_card)

        # Permissions quick toggle
        perm_card, perm_l = _card("Permissions")
        self._perm_checks = {}
        perm_items = [
            ("microphone",     "🎤  Microphone (voice input)"),
            ("screen_capture", "📸  Screen Capture"),
            ("file_read",      "📂  File Read Access"),
            ("pc_control",     "💻  Desktop Control (needs confirmation)"),
            ("memory",         "🧠  Memory Persistence"),
            ("web_browsing",   "🌐  Web Browsing"),
        ]
        for key, label in perm_items:
            cb = QCheckBox(label)
            cb.setChecked(self._core.config.permission(key))
            cb.toggled.connect(lambda c, k=key: self._toggle_perm(k, c))
            perm_l.addWidget(cb)
            self._perm_checks[key] = cb
        ivl.addWidget(perm_card)

        # Personality
        pers_card, pers_l = _card("Personality")
        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Mode:"))
        self._mode_combo_settings = QComboBox()
        from personality.personality_engine import PersonalityMode
        for m in PersonalityMode:
            self._mode_combo_settings.addItem(m.value.capitalize(), m)
        cur = self._core.personality.settings.mode
        for i in range(self._mode_combo_settings.count()):
            if self._mode_combo_settings.itemData(i) == cur:
                self._mode_combo_settings.setCurrentIndex(i); break
        self._mode_combo_settings.currentIndexChanged.connect(self._on_mode_changed)
        mode_row.addWidget(self._mode_combo_settings, 1)
        pers_l.addLayout(mode_row)

        sarc_row = QHBoxLayout()
        sarc_row.addWidget(QLabel("Sarcasm:"))
        self._sarc_slider_settings = QSlider(Qt.Orientation.Horizontal)
        self._sarc_slider_settings.setRange(0, 100)
        self._sarc_slider_settings.setValue(self._core.personality.settings.sarcasm_level)
        self._sarc_lbl_settings = QLabel(str(self._core.personality.settings.sarcasm_level))
        self._sarc_lbl_settings.setFixedWidth(28)
        self._sarc_slider_settings.valueChanged.connect(lambda v: (
            self._core.personality.set_sarcasm(v),
            self._sarc_lbl_settings.setText(str(v))
        ))
        sarc_row.addWidget(self._sarc_slider_settings, 1)
        sarc_row.addWidget(self._sarc_lbl_settings)
        pers_l.addLayout(sarc_row)
        ivl.addWidget(pers_card)

        # About
        about_card, about_l = _card("About MAX AI")
        about_l.addWidget(QLabel("MAX AI — Modular Autonomous eXecutive",
                                  styleSheet="font-weight:bold;font-size:13px;color:#00E5FF;"))
        about_l.addWidget(QLabel("Version 2.0.0 — LEREON Technologies",
                                  styleSheet="color:#4A90B0;font-size:11px;"))
        about_l.addWidget(QLabel("MAX AI © 2026 LEREON Technologies. All rights reserved.",
                                  styleSheet="color:#1A4060;font-size:10px;"))
        site_btn = QPushButton("🌐  lereontech.netlify.app")
        site_btn.setObjectName("ghost")
        from PyQt6.QtCore import QUrl
        from PyQt6.QtGui import QDesktopServices
        site_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://lereontech.netlify.app")))
        about_l.addWidget(site_btn)
        ivl.addWidget(about_card)

        ivl.addStretch()
        scroll.setWidget(inner)
        vl.addWidget(scroll, 1)
        return w

    # ── View Header ───────────────────────────────────────────────────────

    def _view_header(self, title: str, sub: str) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(52)
        bar.setStyleSheet("background:#020E1C;border-bottom:1px solid #0A2A45;")
        hl = QHBoxLayout(bar)
        hl.setContentsMargins(16, 0, 16, 0)
        t = QLabel(title)
        t.setStyleSheet("color:#D0ECF8;font-size:14px;font-weight:bold;")
        s = QLabel(sub)
        s.setStyleSheet("color:#1A5070;font-size:11px;")
        hl.addWidget(t)
        hl.addWidget(s)
        hl.addStretch()
        return bar

    # ── Menu ──────────────────────────────────────────────────────────────

    def _build_menu(self):
        mb = self.menuBar()
        fm = mb.addMenu("File")
        fm.addAction("Settings", lambda: self._nav_to("settings"), "Ctrl+,")
        fm.addAction("New Chat", self._new_conversation, "Ctrl+N")
        fm.addSeparator()
        fm.addAction("Exit", self.close, "Ctrl+Q")
        tm = mb.addMenu("Tools")
        tm.addAction("Multi-Model Collaborate", self._open_collaborate)
        tm.addAction("Run Diagnostics", self._run_diagnostics)
        tm.addAction("Screenshot", lambda: self._chat.inject_message("Take a screenshot"))
        hm = mb.addMenu("Help")
        hm.addAction("About MAX AI", self._show_about)
        hm.addAction("LEREON Technologies Website", lambda: (
            __import__('PyQt6.QtGui', fromlist=['QDesktopServices']).QDesktopServices.openUrl(
                __import__('PyQt6.QtCore', fromlist=['QUrl']).QUrl("https://lereontech.netlify.app")
            )
        ))

    # ── Refresh / Update ──────────────────────────────────────────────────

    def _update_clock(self):
        t = time.strftime("%H:%M")
        d = time.strftime("%b %d")
        if hasattr(self, '_clock'):
            self._clock.setText(f"{t}  {d}")
        if hasattr(self, '_nav_clock'):
            self._nav_clock.setText(f"{t}\n{d}")

    def _refresh_status(self):
        ok = bool(self._core.config.enabled_providers)
        if hasattr(self, '_pill_ai'):
            self._pill_ai.setText("● AI")
            self._pill_ai.setStyleSheet(
                f"color:{'#00FF88' if ok else '#FF3355'}; background:#040F1E;"
                "border:1px solid #0A2A45; border-radius:10px; padding:2px 10px; font-size:10px; font-weight:bold;"
            )
        if hasattr(self, '_pill_prov'):
            prov = self._core.config.default_provider or "—"
            self._pill_prov.setText(prov)

    def _refresh_providers(self):
        if not hasattr(self, '_prov_combo'):
            return
        self._prov_combo.blockSignals(True)
        self._prov_combo.clear()
        self._prov_combo.addItem("Auto", "")
        for name in self._core.config.enabled_providers:
            self._prov_combo.addItem(name.capitalize(), name)
        self._prov_combo.blockSignals(False)

    def _refresh_history(self):
        if not hasattr(self, '_history_view'):
            return
        try:
            hist = self._core.memory.get_history(20)
            if not hist:
                self._history_view.setPlainText("No conversation history yet.")
                return
            lines = []
            for h in hist:
                lines.append(f"You: {h['user']}")
                lines.append(f"MAX: {h['assistant'][:200]}")
                lines.append("")
            self._history_view.setPlainText("\n".join(lines))
        except Exception as e:
            self._history_view.setPlainText(f"Error: {e}")

    def _refresh_kb(self):
        if not hasattr(self, '_kb_list'):
            return
        try:
            self._kb_list.clear()
            docs = self._core.knowledge.list_documents()
            for doc in docs:
                item = QListWidgetItem(f"📄  {doc['name']}  ({doc['size_kb']:.0f} KB)")
                item.setData(Qt.ItemDataRole.UserRole, doc["id"])
                self._kb_list.addItem(item)
            self._kb_status.setText(f"{len(docs)} document(s) in knowledge base")
        except Exception as e:
            self._kb_status.setText(f"Error: {e}")

    def _refresh_workflows(self):
        if not hasattr(self, '_wf_list'):
            return
        try:
            self._wf_list.clear()
            for wf in self._core.automation.list_all():
                st = "🟢" if wf.enabled else "⚫"
                item = QListWidgetItem(f"{st}  {wf.name}  [{wf.trigger.value}]  runs:{wf.run_count}")
                item.setData(Qt.ItemDataRole.UserRole, wf.id)
                self._wf_list.addItem(item)
        except Exception:
            pass

    def _refresh_productivity(self):
        if not hasattr(self, '_todo_list'):
            return
        try:
            self._todo_list.clear()
            for t in self._core.productivity.list_todos():
                icon = "✅" if t.done else "⬜"
                item = QListWidgetItem(f"{icon}  [{t.priority.value[0].upper()}]  {t.title}")
                item.setData(Qt.ItemDataRole.UserRole, t.id)
                self._todo_list.addItem(item)
            self._notes_list.clear()
            for n in self._core.productivity.list_notes():
                item = QListWidgetItem(f"🗒  {n.title}")
                item.setData(Qt.ItemDataRole.UserRole, n.id)
                self._notes_list.addItem(item)
        except Exception:
            pass

    def _on_monitor(self, snap):
        try:
            self._cpu_bar.setValue(int(snap.cpu_percent))
            self._cpu_val.setText(f"{snap.cpu_percent:.0f}%")
            self._ram_bar.setValue(int(snap.ram_percent))
            self._ram_val.setText(f"{snap.ram_percent:.0f}%")
            self._dsk_bar.setValue(int(snap.disk_percent))
            self._dsk_val.setText(f"{snap.disk_percent:.0f}%")
            if snap.battery_percent is not None:
                self._bat_bar.setValue(int(snap.battery_percent))
                self._bat_val.setText(f"{snap.battery_percent:.0f}%")
            else:
                self._bat_val.setText("N/A")
            self._mon_text.setPlainText(self._core.monitor.format_snapshot(snap))
        except Exception:
            pass

    def _on_state_change(self, state: MAXState):
        if hasattr(self, '_core_widget'):
            self._core_widget.set_state(state)
        labels = {
            MAXState.IDLE: "IDLE / READY", MAXState.LISTENING: "LISTENING",
            MAXState.THINKING: "PROCESSING", MAXState.EXECUTING: "EXECUTING",
            MAXState.SPEAKING: "SPEAKING", MAXState.BROWSING: "SEARCHING",
            MAXState.ANALYZING: "ANALYZING", MAXState.ERROR: "ERROR",
            MAXState.OFFLINE: "OFFLINE", MAXState.WAITING_APPROVAL: "WAITING",
        }
        if hasattr(self, '_state_lbl'):
            self._state_lbl.setText(labels.get(state, state.value.upper()))

    # ── Conversation management ───────────────────────────────────────────

    def _new_conversation(self):
        self._core.clear_conversation()
        self._current_conv_id = str(uuid.uuid4())[:8]
        if hasattr(self, '_conv_title_lbl'):
            self._conv_title_lbl.setText("New Conversation")
        if hasattr(self, '_chat'):
            self._chat.clear_history()
        self._refresh_conv_list()

    def _search_convs(self, text: str):
        QTimer.singleShot(300, lambda: self._refresh_conv_list(text))

    def _refresh_conv_list(self, search: str = ""):
        if not hasattr(self, '_conv_list'):
            return
        self._conv_list.clear()
        # Show recent conversations from memory
        try:
            hist = self._core.memory.get_history(30)
            seen = set()
            for h in reversed(hist):
                title = h['user'][:30]
                if title not in seen:
                    seen.add(title)
                    item = QListWidgetItem(f"💬  {title}")
                    self._conv_list.addItem(item)
        except Exception:
            pass

    def _on_conv_selected(self, current, previous):
        pass  # Placeholder for future multi-conv support

    # ── Provider / Personality ────────────────────────────────────────────

    def _on_provider_changed(self, idx: int):
        data = self._prov_combo.itemData(idx)
        if data:
            self._core.config.set("providers", "default", data)
        else:
            # Auto — reset to best available
            pass

    def _on_mode_changed(self, idx: int):
        from personality.personality_engine import PersonalityMode
        mode = self._mode_combo_settings.itemData(idx)
        if mode:
            self._core.personality.set_mode(mode)
            self._core.personality.save_to_config(self._core.config)

    def _toggle_perm(self, key: str, value: bool):
        self._core.config.set("permissions", key, value)
        self._core.config.save()

    # ── Studio ────────────────────────────────────────────────────────────

    def _studio_load(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open File", "",
            "Documents (*.pdf *.docx *.txt *.md *.py *.json *.csv);;All Files (*)"
        )
        if not path:
            return
        content = self._core.studio.read_file(path)
        self._studio_input.setPlainText(content)

    def _studio_run(self):
        content = self._studio_input.toPlainText().strip()
        if not content:
            return
        task = self._studio_task.currentData() or "summarize"
        self._studio_output.setPlainText("Processing…")
        result = self._core.studio.run_task_sync(task, content)
        self._studio_output.setPlainText(result)

    def _studio_save(self):
        content = self._studio_output.toPlainText()
        if not content:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save Output", "", "Text Files (*.txt);;All Files (*)")
        if path:
            Path(path).write_text(content, encoding="utf-8")

    # ── Knowledge base ────────────────────────────────────────────────────

    def _kb_import(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Import Documents", "",
            "Documents (*.pdf *.docx *.txt *.md *.py *.json *.csv *.html);;All Files (*)"
        )
        for path in paths:
            self._core.knowledge.import_file(path)
        self._refresh_kb()

    def _kb_search(self, query: str):
        if not query:
            self._refresh_kb()
            return
        results = self._core.knowledge.search(query)
        self._kb_list.clear()
        for r in results:
            item = QListWidgetItem(f"📄  {r['name']} (score:{r['relevance']})\n   {r['snippet'][:80]}…")
            self._kb_list.addItem(item)
        self._kb_status.setText(f"{len(results)} result(s) for '{query}'")

    def _kb_menu(self, pos):
        from PyQt6.QtWidgets import QMenu
        item = self._kb_list.itemAt(pos)
        if not item:
            return
        doc_id = item.data(Qt.ItemDataRole.UserRole)
        if not doc_id:
            return
        menu = QMenu(self)
        menu.setStyleSheet("QMenu{background:#041020;color:#D0ECF8;border:1px solid #0A2A45;border-radius:6px;}"
                           "QMenu::item{padding:7px 20px;}"
                           "QMenu::item:selected{background:#0A2A45;}")
        del_action = menu.addAction("🗑  Delete")
        if menu.exec(self._kb_list.mapToGlobal(pos)) == del_action:
            self._core.knowledge.delete_document(doc_id)
            self._refresh_kb()

    # ── Memory ────────────────────────────────────────────────────────────

    def _clear_memory(self):
        reply = QMessageBox.question(self, "Clear Memory",
                                     "Delete all conversation history?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self._core.memory.clear()
            self._refresh_history()

    # ── Productivity ──────────────────────────────────────────────────────

    def _add_todo(self):
        title = self._todo_input.text().strip()
        if not title:
            return
        from productivity.productivity_engine import Priority
        self._core.productivity.add_todo(title, priority=Priority.MEDIUM)
        self._todo_input.clear()
        self._refresh_productivity()

    def _complete_todo(self, item):
        tid = item.data(Qt.ItemDataRole.UserRole)
        if tid:
            self._core.productivity.complete_todo(tid)
            self._refresh_productivity()

    def _add_note(self):
        title = self._note_title.text().strip()
        content = self._note_body.toPlainText().strip()
        if not title:
            return
        self._core.productivity.add_note(title, content)
        self._note_title.clear()
        self._note_body.clear()
        self._refresh_productivity()

    # ── Workflow ──────────────────────────────────────────────────────────

    def _wf_new(self):
        from automation.workflow_engine import TriggerType, ActionType, WorkflowStep
        step = WorkflowStep(action=ActionType.WAIT, params={"seconds": 0})
        wf = self._core.automation.create("New Workflow", "", TriggerType.MANUAL, {}, [step])
        self._refresh_workflows()
        self._wf_status.setText(f"Created: {wf.name} [{wf.id}]")

    def _wf_run(self):
        item = self._wf_list.currentItem()
        if not item:
            return
        wf_id = item.data(Qt.ItemDataRole.UserRole)
        if wf_id:
            result = self._core.automation.run_workflow(wf_id)
            self._wf_status.setText(f"Ran: {'OK' if result['ok'] else result.get('error','failed')}")
            self._refresh_workflows()

    def _wf_delete(self):
        item = self._wf_list.currentItem()
        if not item:
            return
        wf_id = item.data(Qt.ItemDataRole.UserRole)
        if wf_id:
            self._core.automation.delete(wf_id)
            self._refresh_workflows()

    # ── Plugins ───────────────────────────────────────────────────────────

    def _plugin_load(self):
        item = self._plugin_list.currentItem()
        if not item:
            return
        pid = item.data(Qt.ItemDataRole.UserRole)
        if pid:
            result = self._core.plugins.load_plugin(pid)
            QMessageBox.information(self, "Plugin", result.get("error", "Loaded OK") if not result.get("ok") else "Loaded OK")
            self._plugin_refresh()

    def _plugin_refresh(self):
        if not hasattr(self, '_plugin_list'):
            return
        self._plugin_list.clear()
        discovered = self._core.plugins.discover()
        for meta in discovered:
            status = "⚠️" if meta.error else "📦"
            item = QListWidgetItem(f"{status}  {meta.name} v{meta.version}")
            item.setData(Qt.ItemDataRole.UserRole, meta.id)
            self._plugin_list.addItem(item)

    # ── Voice ─────────────────────────────────────────────────────────────

    def _toggle_voice(self):
        if not self._voice_active:
            self._voice_active = True
            self._nav_mic.setChecked(True)
            self._core.set_state(MAXState.LISTENING)
            threading.Thread(target=self._do_listen, daemon=True).start()
        else:
            self._stop_voice()

    def _do_listen(self):
        transcript = self._core.voice.listen_once()
        if transcript:
            QTimer.singleShot(0, lambda t=transcript: self._chat.inject_message(t))
        QTimer.singleShot(0, self._stop_voice)

    def _stop_voice(self):
        self._voice_active = False
        self._nav_mic.setChecked(False)
        self._core.set_state(MAXState.IDLE)

    # ── Dialogs ───────────────────────────────────────────────────────────

    def _open_full_settings(self):
        from ui.settings_dialog import SettingsDialog
        dlg = SettingsDialog(self._core.config, self)
        dlg.settings_saved.connect(self._on_settings_saved)
        dlg.exec()

    def _on_settings_saved(self):
        self._core.router.reload()
        self._refresh_providers()
        self._refresh_status()

    def _open_collaborate(self):
        from ui.collaborate_dialog import CollaborateDialog
        CollaborateDialog(self._core, self).exec()

    def _run_diagnostics(self):
        from core.diagnostics import Diagnostics
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            Diagnostics().run_full_check()
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Diagnostics")
        dlg.setText("System diagnostics complete.")
        dlg.setDetailedText(buf.getvalue())
        dlg.exec()

    def _show_about(self):
        QMessageBox.about(self, "About MAX AI",
                          "<b>MAX AI</b> — Modular Autonomous eXecutive<br>"
                          "Version 2.0.0<br><br>"
                          "<b>LEREON Technologies</b><br>"
                          "MAX AI © 2026 LEREON Technologies. All rights reserved.<br>"
                          "<a href='https://lereontech.netlify.app'>lereontech.netlify.app</a>")

    def _show_onboarding(self):
        from ui.onboarding import OnboardingWizard
        wizard = OnboardingWizard(self._core.config, self)
        wizard.completed.connect(self._on_onboarding_done)
        wizard.exec()

    def _on_onboarding_done(self, provider_id: str, api_key: str):
        self._core.router.reload()
        self._refresh_providers()
        self._refresh_status()

    def _clear_chat(self):
        self._chat.clear_history()
        self._core.clear_conversation()

    def closeEvent(self, event):
        reply = QMessageBox.question(self, "Quit MAX AI", "Shut down MAX AI?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self._core.shutdown()
            event.accept()
        else:
            event.ignore()
