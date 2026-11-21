"""MAX AI — Multi-Model Collaboration Dialog — LEREON Technologies"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QCheckBox, QListWidget, QListWidgetItem,
    QProgressBar, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor


class CollabWorker(QThread):
    finished = pyqtSignal(dict)
    error    = pyqtSignal(str)

    def __init__(self, core, task: str, providers: list):
        super().__init__()
        self._core = core
        self._task = task
        self._providers = providers

    def run(self):
        import asyncio
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(
                self._core.collaborate(self._task, self._providers)
            )
            loop.close()
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))


class CollaborateDialog(QDialog):
    def __init__(self, core, parent=None):
        super().__init__(parent)
        self._core = core
        self._worker = None
        self.setWindowTitle("MAX — Multi-Model Collaboration")
        self.setMinimumSize(680, 560)
        self._build()

    def _build(self):
        vl = QVBoxLayout(self)
        vl.setSpacing(10)
        vl.setContentsMargins(16, 16, 16, 16)

        title = QLabel("🤝  Multi-Model Collaboration")
        title.setStyleSheet("color:#00BFFF;font-size:14px;font-weight:bold;")
        vl.addWidget(title)

        note = QLabel(
            "Select 2–4 providers. Each contributes in sequence:\n"
            "Research → Analysis → Review → Synthesis"
        )
        note.setStyleSheet("color:#4090B0;font-size:11px;")
        vl.addWidget(note)

        # Provider checkboxes
        prov_lbl = QLabel("Participating Providers:")
        prov_lbl.setStyleSheet("color:#D0ECF8;font-size:12px;font-weight:bold;margin-top:6px;")
        vl.addWidget(prov_lbl)

        self._prov_checks: dict = {}
        all_providers = ["openai","anthropic","gemini","groq","deepseek","mistral","openrouter","ollama"]
        enabled = self._core.config.enabled_providers
        row = QHBoxLayout()
        for name in all_providers:
            cb = QCheckBox(name.capitalize())
            cb.setEnabled(name in enabled)
            cb.setStyleSheet("color:#90C0D8;font-size:12px;margin-right:8px;")
            if not name in enabled:
                cb.setStyleSheet("color:#2A5070;font-size:12px;margin-right:8px;")
            self._prov_checks[name] = cb
            row.addWidget(cb)
        row.addStretch()
        vl.addLayout(row)

        # Task input
        task_lbl = QLabel("Task / Topic:")
        task_lbl.setStyleSheet("color:#D0ECF8;font-size:12px;font-weight:bold;margin-top:6px;")
        vl.addWidget(task_lbl)

        self._task_input = QTextEdit()
        self._task_input.setMaximumHeight(100)
        self._task_input.setPlaceholderText(
            "Enter a complex task or question for the models to collaborate on…\n\n"
            "Example: Analyze the pros and cons of microservices vs monolithic architecture."
        )
        self._task_input.setStyleSheet(
            "background:#040F1E;color:#D0ECF8;border:1px solid #0A2A45;border-radius:6px;padding:8px;"
        )
        vl.addWidget(self._task_input)

        # Run button
        self._run_btn = QPushButton("▶  Start Collaboration")
        self._run_btn.setObjectName("accent_btn")
        self._run_btn.clicked.connect(self._run)
        self._progress = QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.setVisible(False)
        self._progress.setFixedHeight(6)
        vl.addWidget(self._run_btn)
        vl.addWidget(self._progress)

        # Results
        result_lbl = QLabel("Results:")
        result_lbl.setStyleSheet("color:#D0ECF8;font-size:12px;font-weight:bold;")
        vl.addWidget(result_lbl)

        self._results_view = QTextEdit()
        self._results_view.setReadOnly(True)
        self._results_view.setStyleSheet(
            "background:#030C18;color:#D0ECF8;border:1px solid #0A2A45;"
            "border-radius:6px;padding:8px;font-size:12px;"
        )
        vl.addWidget(self._results_view, 1)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        vl.addWidget(close_btn)

    def _run(self):
        task = self._task_input.toPlainText().strip()
        if not task:
            QMessageBox.warning(self, "No Task", "Please enter a task or question.")
            return
        providers = [name for name, cb in self._prov_checks.items() if cb.isChecked()]
        if len(providers) < 2:
            QMessageBox.warning(self, "Select Providers",
                                "Please select at least 2 providers to collaborate.")
            return

        self._run_btn.setEnabled(False)
        self._progress.setVisible(True)
        self._results_view.setPlainText("Collaboration in progress…")

        self._worker = CollabWorker(self._core, task, providers)
        self._worker.finished.connect(self._on_done)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_done(self, results: dict):
        self._run_btn.setEnabled(True)
        self._progress.setVisible(False)
        lines = []
        for role, content in results.items():
            lines.append(f"{'='*60}")
            lines.append(f"  {role}")
            lines.append(f"{'='*60}")
            lines.append(content)
            lines.append("")
        self._results_view.setPlainText("\n".join(lines))

    def _on_error(self, err: str):
        self._run_btn.setEnabled(True)
        self._progress.setVisible(False)
        self._results_view.setPlainText(f"Collaboration error: {err}")
