"""
MAX AI — Conversation Sidebar
LEREON Technologies

Shows conversation history with search, new chat, rename, delete.
"""

import time
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QLineEdit, QMenu,
    QInputDialog, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QAction, QFont


class ConversationSidebar(QWidget):
    """Left sidebar: branding, new chat, search, conversation list, settings nav."""

    new_chat_requested    = pyqtSignal()
    conversation_selected = pyqtSignal(str)   # conv_id
    conversation_deleted  = pyqtSignal(str)
    settings_requested    = pyqtSignal()
    feature_selected      = pyqtSignal(str)   # feature name

    def __init__(self, db=None, parent=None):
        super().__init__(parent)
        self._db = db
        self._current_id = ""
        self.setFixedWidth(240)
        self.setStyleSheet("""
            QWidget { background: #030C18; color: #D0ECF8; }
            QListWidget {
                background: transparent; border: none; outline: none;
            }
            QListWidget::item {
                padding: 10px 12px; border-radius: 6px; margin: 1px 4px;
                color: #90C0D8; font-size: 12px;
            }
            QListWidget::item:selected {
                background: #0A2A45; color: #D0ECF8;
            }
            QListWidget::item:hover {
                background: #071828; color: #D0ECF8;
            }
            QLineEdit {
                background: #040F1E; border: 1px solid #0A2A45;
                border-radius: 6px; padding: 7px 10px; color: #D0ECF8;
                font-size: 12px;
            }
            QLineEdit:focus { border-color: #00BFFF; }
            QPushButton {
                background: #071828; border: 1px solid #0A2A45;
                border-radius: 6px; padding: 8px 12px;
                color: #90C0D8; font-size: 12px; text-align: left;
            }
            QPushButton:hover { background: #0A2A45; color: #D0ECF8; border-color: #00BFFF; }
            QPushButton#new_chat {
                background: #004A80; color: #D9F8FF;
                border: 1px solid #00BFFF; text-align: center;
            }
            QPushButton#new_chat:hover { background: #0070B0; }
            QPushButton#icon_btn {
                background: transparent; border: none;
                color: #2A5070; font-size: 16px; padding: 4px;
            }
            QPushButton#icon_btn:hover { color: #00BFFF; }
        """)
        self._build()

    def _build(self):
        vl = QVBoxLayout(self)
        vl.setSpacing(0)
        vl.setContentsMargins(0, 0, 0, 0)

        # Branding
        brand = QWidget()
        brand.setStyleSheet("background:#020812;border-bottom:1px solid #0A2A45;")
        brand.setFixedHeight(52)
        bl = QHBoxLayout(brand)
        bl.setContentsMargins(14, 8, 14, 8)
        logo = QLabel("✦ MAX AI")
        logo.setStyleSheet("color:#00BFFF;font-size:15px;font-weight:bold;letter-spacing:2px;")
        bl.addWidget(logo)
        bl.addStretch()
        vl.addWidget(brand)

        # New chat button
        new_btn = QPushButton("✚  New Chat")
        new_btn.setObjectName("new_chat")
        new_btn.setFixedHeight(38)
        new_btn.clicked.connect(self.new_chat_requested)
        wrapper = QWidget()
        wl = QVBoxLayout(wrapper)
        wl.setContentsMargins(10, 10, 10, 6)
        wl.addWidget(new_btn)
        vl.addWidget(wrapper)

        # Search
        self._search = QLineEdit()
        self._search.setPlaceholderText("Search conversations…")
        self._search.textChanged.connect(self._on_search)
        sw = QWidget()
        sl = QVBoxLayout(sw)
        sl.setContentsMargins(10, 2, 10, 4)
        sl.addWidget(self._search)
        vl.addWidget(sw)

        # Section: Conversations
        sec_lbl = QLabel("CONVERSATIONS")
        sec_lbl.setStyleSheet("color:#1A4060;font-size:10px;letter-spacing:1px;padding:4px 14px 2px;")
        vl.addWidget(sec_lbl)

        self._conv_list = QListWidget()
        self._conv_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._conv_list.customContextMenuRequested.connect(self._context_menu)
        self._conv_list.currentItemChanged.connect(self._on_selection)
        vl.addWidget(self._conv_list, 1)

        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet("color:#0A2A45;margin:4px 10px;")
        vl.addWidget(div)

        # Feature nav
        features = [
            ("💬", "Chat",         "chat"),
            ("🗂", "Studio",       "studio"),
            ("✅", "Productivity", "productivity"),
            ("📚", "Knowledge",    "knowledge"),
            ("⚙", "Automation",   "automation"),
            ("📊", "Monitor",      "monitor"),
        ]
        for icon, label, fid in features:
            btn = QPushButton(f"{icon}  {label}")
            btn.setFixedHeight(34)
            btn.clicked.connect(lambda checked=False, f=fid: self.feature_selected.emit(f))
            fw = QWidget()
            fl = QVBoxLayout(fw)
            fl.setContentsMargins(10, 1, 10, 1)
            fl.setSpacing(0)
            fl.addWidget(btn)
            vl.addWidget(fw)

        # Settings + about
        div2 = QFrame()
        div2.setFrameShape(QFrame.Shape.HLine)
        div2.setStyleSheet("color:#0A2A45;margin:4px 10px;")
        vl.addWidget(div2)

        settings_btn = QPushButton("⚙  Settings")
        settings_btn.setFixedHeight(34)
        settings_btn.clicked.connect(self.settings_requested)
        sw2 = QWidget()
        sl2 = QVBoxLayout(sw2)
        sl2.setContentsMargins(10, 2, 10, 2)
        sl2.addWidget(settings_btn)
        vl.addWidget(sw2)

        footer = QLabel("LEREON Technologies")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet("color:#0A2A40;font-size:9px;padding:6px;")
        vl.addWidget(footer)

    # ── Data management ───────────────────────────────────────────────────

    def refresh(self, search: str = ""):
        """Reload conversations from DB."""
        self._conv_list.clear()
        if not self._db:
            return
        try:
            if search.strip():
                convs = self._db.search_conversations(search)
            else:
                convs = self._db.list_conversations(limit=100)

            if not convs:
                item = QListWidgetItem("No conversations yet")
                item.setFlags(Qt.ItemFlag.NoItemFlags)
                item.setForeground(QColor("#1A4060"))
                self._conv_list.addItem(item)
                return

            for c in convs:
                title = c.get("title", "New conversation")
                ts = c.get("updated_at", 0)
                age = self._age_str(ts)
                item = QListWidgetItem(f"{title[:28]}\n{age}")
                item.setData(Qt.ItemDataRole.UserRole, c["id"])
                if c["id"] == self._current_id:
                    item.setForeground(QColor("#D9F8FF"))
                else:
                    item.setForeground(QColor("#90C0D8"))
                self._conv_list.addItem(item)
        except Exception as e:
            item = QListWidgetItem(f"Error: {str(e)[:40]}")
            item.setForeground(QColor("#FF4455"))
            self._conv_list.addItem(item)

    def set_current(self, conv_id: str):
        self._current_id = conv_id
        for i in range(self._conv_list.count()):
            item = self._conv_list.item(i)
            if item and item.data(Qt.ItemDataRole.UserRole) == conv_id:
                self._conv_list.setCurrentItem(item)
                break

    def _age_str(self, ts: float) -> str:
        if not ts:
            return ""
        diff = time.time() - ts
        if diff < 60:
            return "just now"
        if diff < 3600:
            return f"{int(diff/60)}m ago"
        if diff < 86400:
            return f"{int(diff/3600)}h ago"
        return f"{int(diff/86400)}d ago"

    # ── Event handlers ────────────────────────────────────────────────────

    def _on_search(self, text: str):
        QTimer.singleShot(300, lambda: self.refresh(text))

    def _on_selection(self, current, previous):
        if not current:
            return
        conv_id = current.data(Qt.ItemDataRole.UserRole)
        if conv_id and conv_id != self._current_id:
            self._current_id = conv_id
            self.conversation_selected.emit(conv_id)

    def _context_menu(self, pos):
        item = self._conv_list.itemAt(pos)
        if not item:
            return
        conv_id = item.data(Qt.ItemDataRole.UserRole)
        if not conv_id:
            return

        menu = QMenu(self)
        menu.setStyleSheet(
            "QMenu{background:#040F1E;color:#D0ECF8;border:1px solid #0A2A45;border-radius:6px;}"
            "QMenu::item{padding:7px 20px;}"
            "QMenu::item:selected{background:#004A80;}"
        )
        rename_action = menu.addAction("✏  Rename")
        menu.addSeparator()
        delete_action = menu.addAction("🗑  Delete")

        action = menu.exec(self._conv_list.mapToGlobal(pos))
        if action == rename_action:
            self._rename_conversation(conv_id, item)
        elif action == delete_action:
            self._delete_conversation(conv_id)

    def _rename_conversation(self, conv_id: str, item: QListWidgetItem):
        current_title = item.text().split("\n")[0]
        new_title, ok = QInputDialog.getText(
            self, "Rename Conversation", "New title:", text=current_title
        )
        if ok and new_title.strip():
            if self._db:
                self._db.update_conversation_title(conv_id, new_title.strip())
            self.refresh()

    def _delete_conversation(self, conv_id: str):
        reply = QMessageBox.question(
            self, "Delete Conversation",
            "Delete this conversation? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self._db:
                self._db.delete_conversation(conv_id)
            self.conversation_deleted.emit(conv_id)
            self.refresh()
