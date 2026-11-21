"""MAX AI — Plugin Manager Dialog — LEREON Technologies"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QPushButton, QTextEdit, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor


class PluginDialog(QDialog):
    def __init__(self, core, parent=None):
        super().__init__(parent)
        self._core = core
        self.setWindowTitle("MAX — Plugin Manager")
        self.setMinimumSize(620, 480)
        self._build()
        self._refresh()

    def _build(self):
        vl = QVBoxLayout(self)
        vl.setSpacing(10)
        vl.setContentsMargins(16, 16, 16, 16)

        title = QLabel("🔌  Plugin Manager")
        title.setStyleSheet("color:#00BFFF;font-size:14px;font-weight:bold;")
        vl.addWidget(title)

        note = QLabel(
            "Plugins extend MAX AI without modifying core code.\n"
            f"Place .py plugin files in: plugins/installed/"
        )
        note.setStyleSheet("color:#4090B0;font-size:11px;")
        vl.addWidget(note)

        # Discovered plugins
        disc_lbl = QLabel("Discovered Plugins:")
        disc_lbl.setStyleSheet("color:#D0ECF8;font-size:12px;font-weight:bold;")
        vl.addWidget(disc_lbl)

        self._disc_list = QListWidget()
        self._disc_list.setMaximumHeight(160)
        self._disc_list.setStyleSheet(
            "background:#040F1E;border:1px solid #0A2A45;border-radius:6px;"
            "color:#D0ECF8;font-size:12px;"
        )
        self._disc_list.currentRowChanged.connect(self._on_select)
        vl.addWidget(self._disc_list)

        btn_row = QHBoxLayout()
        load_btn = QPushButton("▶  Load Plugin")
        load_btn.clicked.connect(self._load)
        unload_btn = QPushButton("⏹  Unload Plugin")
        unload_btn.clicked.connect(self._unload)
        refresh_btn = QPushButton("🔄  Refresh")
        refresh_btn.clicked.connect(self._refresh)
        for b in [load_btn, unload_btn, refresh_btn]:
            btn_row.addWidget(b)
        btn_row.addStretch()
        vl.addLayout(btn_row)

        # Loaded plugins
        loaded_lbl = QLabel("Loaded Plugins:")
        loaded_lbl.setStyleSheet("color:#D0ECF8;font-size:12px;font-weight:bold;margin-top:8px;")
        vl.addWidget(loaded_lbl)

        self._loaded_list = QListWidget()
        self._loaded_list.setMaximumHeight(130)
        self._loaded_list.setStyleSheet(
            "background:#040F1E;border:1px solid #0A2A45;border-radius:6px;"
            "color:#D0ECF8;font-size:12px;"
        )
        vl.addWidget(self._loaded_list)

        # Detail view
        self._detail = QTextEdit()
        self._detail.setReadOnly(True)
        self._detail.setMaximumHeight(100)
        self._detail.setStyleSheet(
            "background:#030C18;color:#4090B0;border:1px solid #0A2A45;"
            "border-radius:6px;padding:6px;font-size:11px;"
        )
        self._detail.setPlainText(
            "Plugins directory: plugins/installed/\n"
            "Drop .py plugin files there, then click Refresh."
        )
        vl.addWidget(self._detail)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        vl.addWidget(close_btn)

    def _refresh(self):
        self._disc_list.clear()
        self._discovered = self._core.plugins.discover()
        for meta in self._discovered:
            status = "⚠️" if meta.error else "📦"
            item = QListWidgetItem(f"{status} {meta.name} v{meta.version} — {meta.description[:50]}")
            item.setData(Qt.ItemDataRole.UserRole, meta.id)
            if meta.error:
                item.setForeground(QColor("#FF4455"))
            else:
                item.setForeground(QColor("#D0ECF8"))
            self._disc_list.addItem(item)

        self._loaded_list.clear()
        for meta in self._core.plugins.loaded_plugins:
            item = QListWidgetItem(f"✅ {meta.name} v{meta.version} by {meta.author}")
            item.setData(Qt.ItemDataRole.UserRole, meta.id)
            item.setForeground(QColor("#00FF88"))
            self._loaded_list.addItem(item)

    def _on_select(self, idx: int):
        if idx < 0 or idx >= len(self._discovered):
            return
        meta = self._discovered[idx]
        txt = f"ID: {meta.id}\nName: {meta.name}\nVersion: {meta.version}\n"
        txt += f"Author: {meta.author}\nDescription: {meta.description}\n"
        if meta.permissions_required:
            txt += f"Requires: {', '.join(meta.permissions_required)}\n"
        if meta.error:
            txt += f"\nError: {meta.error}"
        self._detail.setPlainText(txt)

    def _load(self):
        item = self._disc_list.currentItem()
        if not item:
            return
        plugin_id = item.data(Qt.ItemDataRole.UserRole)
        result = self._core.plugins.load_plugin(plugin_id)
        if result["ok"]:
            QMessageBox.information(self, "Plugin Loaded",
                                    f"Plugin '{plugin_id}' loaded successfully.")
        else:
            QMessageBox.warning(self, "Load Failed", result["error"])
        self._refresh()

    def _unload(self):
        item = self._loaded_list.currentItem()
        if not item:
            return
        plugin_id = item.data(Qt.ItemDataRole.UserRole)
        ok = self._core.plugins.unload_plugin(plugin_id)
        if ok:
            QMessageBox.information(self, "Plugin Unloaded", f"'{plugin_id}' unloaded.")
        else:
            QMessageBox.warning(self, "Error", f"Could not unload '{plugin_id}'.")
        self._refresh()
