"""
MAX AI — Chat Widget (Streaming Edition)
LEREON Technologies

Features:
- Streaming responses (tokens appear as they arrive)
- Markdown rendering in messages
- Copy response button
- Voice input (thread-safe)
- Clear loading/error states
- Attach image for vision analysis
"""

import time
import asyncio
import threading
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextBrowser,
    QPushButton, QLabel, QSizePolicy, QFileDialog, QApplication
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QObject
from PyQt6.QtGui import QKeyEvent, QColor, QFont


# ── Streaming worker ──────────────────────────────────────────────────────

class StreamWorker(QThread):
    """Runs streaming completion in background thread, emits chunks."""
    chunk     = pyqtSignal(str)      # each text chunk
    finished  = pyqtSignal(str, str, float, int)  # provider, model, ms, tokens
    error     = pyqtSignal(str)

    def __init__(self, core, text: str, provider: str = None, image_path: str = None):
        super().__init__()
        self._core     = core
        self._text     = text
        self._provider = provider
        self._image_path = image_path
        self._full_text = ""
        self._start    = time.time()

    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._stream())
            loop.close()
        except Exception as e:
            self.error.emit(str(e))

    async def _stream(self):
        from core.max_core import MAXState
        self._core.set_state(MAXState.THINKING)

        # Build messages
        ctx = ""
        if self._core.config.memory_enabled:
            try:
                ctx = self._core.memory.get_context(self._text)
            except Exception:
                pass
        kb_ctx = ""
        try:
            kb_ctx = self._core.knowledge.get_context_for_query(self._text)
        except Exception:
            pass
        msgs = self._core._build_messages(ctx, kb_ctx)

        system_prompt = self._core.personality.build_system_prompt()

        # Select provider
        pname = self._provider or self._core.config.default_provider
        provider = None
        if pname:
            try:
                provider = self._core.router.get(pname)
            except Exception:
                pass
        if provider is None:
            provider = self._core.router.get_fallback(exclude=[pname] if pname else [])

        if provider is None:
            self.error.emit(
                "⚠️ **No AI providers available.**\n\n"
                "Add an API key in **Settings → Open Full Settings Dialog**."
            )
            return

        self._core.set_state(MAXState.THINKING)
        tokens = 0
        model = provider.model

        # Try streaming first
        if hasattr(provider, "stream"):
            try:
                async for chunk_text in provider.stream(messages=msgs, system=system_prompt):
                    self._full_text += chunk_text
                    self.chunk.emit(chunk_text)
                self._core.set_state(MAXState.IDLE)
            except Exception:
                # Fall back to non-streaming
                self._full_text = ""
                try:
                    resp_text, model, tokens = await provider.complete(
                        messages=msgs, system=system_prompt
                    )
                    self._full_text = resp_text
                    self.chunk.emit(resp_text)
                except Exception as e:
                    self.error.emit(str(e))
                    return
        else:
            try:
                resp_text, model, tokens = await provider.complete(
                    messages=msgs, system=system_prompt
                )
                self._full_text = resp_text
                self.chunk.emit(resp_text)
            except Exception as e:
                self.error.emit(str(e))
                return

        # Store in conversation + memory
        from core.max_core import ChatMessage
        self._core.conversation.append(ChatMessage(
            role="assistant",
            content=self._full_text,
            provider=provider.name,
            tokens=tokens
        ))
        if self._core.config.memory_enabled:
            try:
                self._core.memory.store(self._text, self._full_text)
            except Exception:
                pass

        ms = (time.time() - self._start) * 1000
        self._core.set_state(MAXState.IDLE)
        self.finished.emit(provider.name, model, ms, tokens)


# ── Message HTML helpers ──────────────────────────────────────────────────

def _md_to_html(text: str) -> str:
    """Minimal markdown → HTML for chat display."""
    import re
    t = text
    # Code blocks
    t = re.sub(
        r'```(\w*)\n?(.*?)```',
        lambda m: (
            f'<pre style="background:#020C18;color:#00E5FF;padding:10px 12px;'
            f'border-radius:6px;border:1px solid #0A2A45;font-family:monospace;'
            f'font-size:12px;overflow:auto;white-space:pre;">{m.group(2)}</pre>'
        ),
        t, flags=re.DOTALL
    )
    # Inline code
    t = re.sub(
        r'`([^`]+)`',
        r'<code style="background:#020C18;color:#00BFFF;padding:2px 6px;'
        r'border-radius:3px;font-family:monospace;font-size:12px;">\1</code>',
        t
    )
    # Bold
    t = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', t)
    # Italic
    t = re.sub(r'\*(.+?)\*', r'<i>\1</i>', t)
    # H1-H3
    t = re.sub(r'^### (.+)$', r'<b style="color:#00BFFF;font-size:13px;">\1</b>', t, flags=re.MULTILINE)
    t = re.sub(r'^## (.+)$',  r'<b style="color:#00BFFF;font-size:14px;">\1</b>', t, flags=re.MULTILINE)
    t = re.sub(r'^# (.+)$',   r'<b style="color:#00BFFF;font-size:15px;">\1</b>', t, flags=re.MULTILINE)
    # Bullet lists
    t = re.sub(r'^[•\-\*] (.+)$', r'&nbsp;&nbsp;• \1', t, flags=re.MULTILINE)
    # Numbered lists
    t = re.sub(r'^(\d+)\. (.+)$', r'&nbsp;&nbsp;\1. \2', t, flags=re.MULTILINE)
    # Newlines
    t = t.replace('\n\n', '<br><br>').replace('\n', '<br>')
    return t


def _user_html(text: str, ts: str) -> str:
    safe = text.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
    safe = safe.replace('\n', '<br>')
    return (
        f'<div style="text-align:right;margin:8px 4px 8px 60px;">'
        f'<div style="display:inline-block;background:#0A2A45;color:#D9F8FF;'
        f'border-radius:14px 14px 2px 14px;padding:10px 14px;font-size:13px;'
        f'line-height:1.5;max-width:92%;text-align:left;">'
        f'{safe}</div>'
        f'<div style="color:#1A4060;font-size:10px;margin-top:3px;">{ts}</div>'
        f'</div>'
    )


def _max_html(text: str, ts: str, provider: str, model: str, ms: float, tokens: int, msg_id: str) -> str:
    body = _md_to_html(text)
    meta_parts = []
    if provider and provider != "none":
        meta_parts.append(f"{provider}")
    if model:
        meta_parts.append(model)
    if ms > 0:
        meta_parts.append(f"{ms:.0f}ms")
    if tokens > 0:
        meta_parts.append(f"{tokens}t")
    meta = " · ".join(meta_parts)
    return (
        f'<div style="text-align:left;margin:8px 60px 8px 4px;">'
        f'<div style="color:#00BFFF;font-size:10px;font-weight:bold;'
        f'margin-bottom:4px;letter-spacing:0.5px;">▸ MAX</div>'
        f'<div id="{msg_id}" style="display:inline-block;background:#041020;color:#D0ECF8;'
        f'border:1px solid #0A2A45;border-radius:2px 14px 14px 14px;'
        f'padding:10px 14px;font-size:13px;line-height:1.6;max-width:95%;">'
        f'{body}</div>'
        f'<div style="color:#1A4060;font-size:10px;margin-top:3px;">'
        f'{ts} · {meta}</div>'
        f'</div>'
    )


def _system_html(text: str) -> str:
    return (
        f'<div style="text-align:center;margin:6px 20px;">'
        f'<span style="color:#1A5070;font-size:11px;font-style:italic;">{text}</span>'
        f'</div>'
    )


def _thinking_html() -> str:
    return (
        f'<div id="__thinking__" style="text-align:left;margin:8px 60px 8px 4px;">'
        f'<div style="color:#00BFFF;font-size:10px;font-weight:bold;margin-bottom:4px;">▸ MAX</div>'
        f'<div style="display:inline-block;background:#041020;border:1px solid #0A2A45;'
        f'border-radius:2px 14px 14px 14px;padding:10px 14px;">'
        f'<span style="color:#AA44FF;font-size:13px;">● thinking…</span></div>'
        f'</div>'
    )


# ── Chat Widget ───────────────────────────────────────────────────────────

class ChatWidget(QWidget):
    """Main chat interface with streaming responses."""

    def __init__(self, core, parent=None):
        super().__init__(parent)
        self._core          = core
        self._worker        = None
        self._busy          = False
        self._streaming_id  = ""
        self._streaming_buf = ""
        self._last_response = ""
        self._attached_image: str = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # Chat display
        self._display = QTextBrowser()
        self._display.setOpenExternalLinks(True)
        self._display.setReadOnly(True)
        self._display.setStyleSheet(
            "QTextBrowser { background:#020812; border:none; padding:12px 8px; }"
        )
        layout.addWidget(self._display, 1)

        # Action bar (copy last, attach image)
        self._action_bar = QWidget()
        self._action_bar.setStyleSheet("background:#020812;")
        ab_l = QHBoxLayout(self._action_bar)
        ab_l.setContentsMargins(12, 2, 12, 2)
        ab_l.setSpacing(6)

        self._copy_btn = QPushButton("⎘  Copy Last Response")
        self._copy_btn.setObjectName("ghost")
        self._copy_btn.setFixedHeight(26)
        self._copy_btn.setStyleSheet(
            "QPushButton{background:transparent;border:none;color:#1A5070;"
            "font-size:11px;padding:2px 8px;}"
            "QPushButton:hover{color:#00BFFF;}"
        )
        self._copy_btn.clicked.connect(self._copy_last)
        self._copy_btn.setVisible(False)

        self._attach_lbl = QLabel()
        self._attach_lbl.setStyleSheet("color:#004A80;font-size:10px;")

        self._attach_btn = QPushButton("📎  Image")
        self._attach_btn.setObjectName("ghost")
        self._attach_btn.setFixedHeight(26)
        self._attach_btn.setStyleSheet(
            "QPushButton{background:transparent;border:none;color:#1A5070;"
            "font-size:11px;padding:2px 8px;}"
            "QPushButton:hover{color:#00BFFF;}"
        )
        self._attach_btn.clicked.connect(self._attach_image)
        self._attach_btn.setToolTip("Attach an image for vision analysis")

        ab_l.addWidget(self._copy_btn)
        ab_l.addWidget(self._attach_lbl)
        ab_l.addStretch()
        ab_l.addWidget(self._attach_btn)
        layout.addWidget(self._action_bar)

        # Streaming indicator
        self._stream_lbl = QLabel()
        self._stream_lbl.setVisible(False)
        self._stream_lbl.setStyleSheet(
            "color:#AA44FF;font-size:11px;padding:3px 14px;"
            "background:#020E1C;border-top:1px solid #0A2A45;"
        )
        layout.addWidget(self._stream_lbl)

        # Input area
        input_area = QWidget()
        input_area.setStyleSheet("background:#020E1C;border-top:1px solid #0A2A45;")
        ia_l = QHBoxLayout(input_area)
        ia_l.setContentsMargins(10, 8, 10, 10)
        ia_l.setSpacing(8)

        self._input = _ChatInput()
        self._input.setPlaceholderText("Message MAX…   Enter to send · Shift+Enter for new line")
        self._input.send_requested.connect(self._send)
        ia_l.addWidget(self._input, 1)

        self._send_btn = QPushButton("Send")
        self._send_btn.setObjectName("primary")
        self._send_btn.setFixedSize(72, 40)
        self._send_btn.clicked.connect(self._send)
        ia_l.addWidget(self._send_btn)

        self._mic_btn = QPushButton("🎤")
        self._mic_btn.setObjectName("icon_btn")
        self._mic_btn.setFixedSize(40, 40)
        self._mic_btn.setToolTip("Voice input")
        self._mic_btn.clicked.connect(self._voice_input)
        ia_l.addWidget(self._mic_btn)

        layout.addWidget(input_area)

        # Welcome
        self._append_system("MAX AI ready. How can I help you today?")

    # ── Message rendering ─────────────────────────────────────────────────

    def _append_system(self, text: str):
        self._display.append(_system_html(text))
        self._scroll()

    def _append_user(self, text: str):
        ts = time.strftime("%H:%M")
        self._display.append(_user_html(text, ts))
        self._scroll()

    def _start_streaming_bubble(self) -> str:
        """Insert a placeholder bubble that we'll fill in as chunks arrive."""
        import uuid
        msg_id = f"msg_{uuid.uuid4().hex[:8]}"
        self._streaming_id  = msg_id
        self._streaming_buf = ""
        self._display.append(_thinking_html())
        self._scroll()
        return msg_id

    def _append_chunk(self, chunk: str):
        """Append streaming chunk to the in-progress bubble."""
        self._streaming_buf += chunk
        # Rebuild the display with current buffer
        html = self._display.toHtml()
        # Replace thinking indicator with current content
        body = _md_to_html(self._streaming_buf)
        new_bubble = (
            f'<div style="display:inline-block;background:#041020;color:#D0ECF8;'
            f'border:1px solid #0A2A45;border-radius:2px 14px 14px 14px;'
            f'padding:10px 14px;font-size:13px;line-height:1.6;max-width:95%;">'
            f'{body}</div>'
        )
        if '__thinking__' in html:
            # Replace the thinking div with the growing response
            import re
            html = re.sub(
                r'<div id="__thinking__".*?</div>\s*</div>',
                f'<div style="text-align:left;margin:8px 60px 8px 4px;">'
                f'<div style="color:#00BFFF;font-size:10px;font-weight:bold;margin-bottom:4px;">▸ MAX</div>'
                f'{new_bubble}'
                f'<div style="color:#1A4060;font-size:10px;margin-top:3px;">streaming…</div>'
                f'</div>',
                html, flags=re.DOTALL
            )
            self._display.setHtml(html)
        self._scroll()

    def _finalize_bubble(self, provider: str, model: str, ms: float, tokens: int):
        """Replace streaming bubble with final formatted version."""
        ts = time.strftime("%H:%M")
        import re
        html = self._display.toHtml()
        # Remove the in-progress bubble
        html = re.sub(
            r'<div style="text-align:left;margin:8px 60px 8px 4px;">.*?streaming….*?</div>\s*</div>',
            '',
            html, flags=re.DOTALL
        )
        self._display.setHtml(html)
        # Append the final formatted bubble
        final_html = _max_html(
            self._streaming_buf, ts, provider, model, ms, tokens, self._streaming_id
        )
        self._display.append(final_html)
        self._last_response = self._streaming_buf
        self._copy_btn.setVisible(True)
        self._scroll()

    def _scroll(self):
        sb = self._display.verticalScrollBar()
        sb.setValue(sb.maximum())

    # ── Send ──────────────────────────────────────────────────────────────

    def _send(self):
        if self._busy:
            return
        text = self._input.toPlainText().strip()
        if not text:
            return
        self._input.clear()

        # Append user message to core conversation
        from core.max_core import ChatMessage
        self._core.conversation.append(ChatMessage(role="user", content=text))

        self._append_user(text)
        self._start_streaming_bubble()
        self._set_busy(True)

        image_path = self._attached_image
        self._attached_image = None
        self._attach_lbl.setText("")

        self._worker = StreamWorker(
            self._core, text,
            provider=self._core.config.default_provider or None,
            image_path=image_path
        )
        self._worker.chunk.connect(self._on_chunk)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_chunk(self, chunk: str):
        self._append_chunk(chunk)
        self._stream_lbl.setText(f"● streaming  {len(self._streaming_buf)} chars")

    def _on_finished(self, provider: str, model: str, ms: float, tokens: int):
        self._finalize_bubble(provider, model, ms, tokens)
        self._stream_lbl.setVisible(False)
        self._set_busy(False)
        # Speak if voice output enabled
        if self._core.config.voice_output_enabled:
            try:
                self._core.voice.speak(self._last_response)
            except Exception:
                pass

    def _on_error(self, err: str):
        # Remove thinking bubble
        import re
        html = self._display.toHtml()
        html = re.sub(r'<div id="__thinking__".*?</div>\s*</div>', '', html, flags=re.DOTALL)
        self._display.setHtml(html)
        self._append_system(f"❌ {err}")
        self._stream_lbl.setVisible(False)
        self._set_busy(False)

    def _set_busy(self, busy: bool):
        self._busy = busy
        self._send_btn.setEnabled(not busy)
        self._send_btn.setText("…" if busy else "Send")
        self._stream_lbl.setVisible(busy)
        if busy:
            self._stream_lbl.setText("● connecting…")

    # ── Copy response ─────────────────────────────────────────────────────

    def _copy_last(self):
        if self._last_response:
            QApplication.clipboard().setText(self._last_response)
            self._copy_btn.setText("⎘  Copied!")
            QTimer.singleShot(1500, lambda: self._copy_btn.setText("⎘  Copy Last Response"))

    # ── Attach image ──────────────────────────────────────────────────────

    def _attach_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Attach Image", "",
            "Images (*.png *.jpg *.jpeg *.webp *.gif);;All Files (*)"
        )
        if path:
            self._attached_image = path
            name = Path(path).name
            self._attach_lbl.setText(f"📎 {name}")
            self._append_system(f"Image attached: {name}. Ask a question about it.")

    # ── Voice input ───────────────────────────────────────────────────────

    def _voice_input(self):
        if self._busy:
            return
        self._mic_btn.setEnabled(False)
        self._mic_btn.setText("🔴")
        self._append_system("Listening…")

        def _listen():
            try:
                text = self._core.voice.listen_once()
                if text:
                    QTimer.singleShot(0, lambda t=text: self._on_voice_transcript(t))
                else:
                    QTimer.singleShot(0, lambda: self._append_system("Could not understand. Try again."))
            except Exception as e:
                QTimer.singleShot(0, lambda err=str(e): self._append_system(f"Voice error: {err}"))
            finally:
                QTimer.singleShot(0, self._reset_mic_btn)

        threading.Thread(target=_listen, daemon=True).start()

    def _on_voice_transcript(self, text: str):
        self._input.setPlainText(text)
        self._send()

    def _reset_mic_btn(self):
        self._mic_btn.setEnabled(True)
        self._mic_btn.setText("🎤")

    # ── Public API ────────────────────────────────────────────────────────

    def inject_message(self, text: str):
        """Send a message programmatically (e.g. from quick actions)."""
        self._input.setPlainText(text)
        self._send()

    def clear_history(self):
        self._display.clear()
        self._last_response = ""
        self._copy_btn.setVisible(False)
        self._append_system("Conversation cleared.")


class _ChatInput(QTextBrowser):
    """Multi-line input: Enter sends, Shift+Enter adds newline."""
    send_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(False)
        self.setMaximumHeight(110)
        self.setMinimumHeight(44)
        self.setAcceptRichText(False)
        self.setStyleSheet(
            "QTextBrowser { background:#041020; color:#D0ECF8; border:none;"
            "font-size:13px; padding:8px 10px; border-radius:8px; }"
        )

    def keyPressEvent(self, e: QKeyEvent):
        if e.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if e.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                super().keyPressEvent(e)
            else:
                self.send_requested.emit()
        else:
            super().keyPressEvent(e)
