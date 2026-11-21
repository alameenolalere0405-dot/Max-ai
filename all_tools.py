"""
MAX AI — All Built-in Tools
Each tool is a self-contained class. Register them in tools/registry.py.
"""

import logging
import asyncio
import ast
import operator
import os
import sys
import time
from pathlib import Path
from datetime import datetime, timezone
from abc import ABC, abstractmethod

logger = logging.getLogger("MAX.tools")

# ─────────────────────────────────────────────
# BASE TOOL
# ─────────────────────────────────────────────

class BaseTool(ABC):
    name: str = "base"
    description: str = ""
    permission_key: str = ""          # config permission key; "" = always allowed
    requires_confirmation: bool = False

    def allowed(self, config) -> bool:
        if not self.permission_key:
            return True
        return config.permission(self.permission_key)

    @abstractmethod
    async def run(self, **kwargs) -> str:
        ...

    def __repr__(self):
        return f"<Tool:{self.name}>"


# ─────────────────────────────────────────────
# CALCULATOR
# ─────────────────────────────────────────────

_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub,
    ast.Mult: operator.mul, ast.Div: operator.truediv,
    ast.Pow: operator.pow, ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
    ast.USub: operator.neg, ast.UAdd: operator.pos,
}


def _safe_eval(node):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("Non-numeric literal")
    if isinstance(node, ast.BinOp):
        return _OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp):
        return _OPS[type(node.op)](_safe_eval(node.operand))
    raise ValueError(f"Unsupported: {type(node).__name__}")


class CalculatorTool(BaseTool):
    name = "calculate"
    description = "Evaluate a mathematical expression safely (e.g. '2 ** 10 + 55 / 5')"

    async def run(self, expression: str = "", **kwargs) -> str:
        expr = (expression or kwargs.get("input", "")).strip()
        if not expr:
            return "No expression provided."
        try:
            tree = ast.parse(expr, mode="eval")
            result = _safe_eval(tree.body)
            return f"{expr} = {result}"
        except Exception as e:
            return f"Cannot evaluate '{expr}': {e}"


# ─────────────────────────────────────────────
# DATE / TIME
# ─────────────────────────────────────────────

class DateTimeTool(BaseTool):
    name = "datetime"
    description = "Return the current local date and time"

    async def run(self, **kwargs) -> str:
        now = datetime.now()
        utc = datetime.now(timezone.utc)
        return (
            f"Local: {now.strftime('%A, %B %d, %Y — %I:%M:%S %p')}\n"
            f"UTC:   {utc.strftime('%Y-%m-%d %H:%M:%S UTC')}"
        )


# ─────────────────────────────────────────────
# SYSTEM INFO
# ─────────────────────────────────────────────

class SystemInfoTool(BaseTool):
    name = "system_info"
    description = "Return CPU, RAM, disk usage and OS details"

    async def run(self, **kwargs) -> str:
        try:
            import psutil, platform
            cpu = await asyncio.to_thread(psutil.cpu_percent, 1)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            return (
                f"OS:   {platform.system()} {platform.release()} ({platform.machine()})\n"
                f"CPU:  {cpu:.1f}% used  ({psutil.cpu_count(logical=True)} logical cores)\n"
                f"RAM:  {mem.percent:.1f}% used  ({mem.used // 1024**2} MB / {mem.total // 1024**2} MB)\n"
                f"Disk: {disk.percent:.1f}% used  ({disk.used // 1024**3} GB / {disk.total // 1024**3} GB)"
            )
        except ImportError:
            return "psutil not installed — run: pip install psutil"
        except Exception as e:
            return f"System info error: {e}"


# ─────────────────────────────────────────────
# CLIPBOARD
# ─────────────────────────────────────────────

class ClipboardTool(BaseTool):
    name = "clipboard"
    description = "Read or write the system clipboard. Args: action='read'|'write', text='...' (for write)"

    async def run(self, action: str = "read", text: str = "", **kwargs) -> str:
        try:
            import pyperclip
        except ImportError:
            return "pyperclip not installed — run: pip install pyperclip"
        try:
            if action == "read":
                content = await asyncio.to_thread(pyperclip.paste)
                return f"Clipboard: {content[:800]}" if content else "Clipboard is empty."
            elif action == "write":
                if not text:
                    return "No text provided to copy."
                await asyncio.to_thread(pyperclip.copy, text)
                return f"Copied to clipboard ({len(text)} chars)."
            return f"Unknown clipboard action: {action}"
        except Exception as e:
            return f"Clipboard error: {e}"


# ─────────────────────────────────────────────
# WEB FETCH
# ─────────────────────────────────────────────

class WebFetchTool(BaseTool):
    name = "web_fetch"
    description = "Fetch and return the main text content of a URL"
    permission_key = "web_browsing"

    async def run(self, url: str = "", **kwargs) -> str:
        if not url:
            return "No URL provided."
        if not url.startswith(("http://", "https://")):
            return f"Invalid URL (must start with http/https): {url}"
        try:
            import aiohttp
            from bs4 import BeautifulSoup
            headers = {"User-Agent": "Mozilla/5.0 (compatible; MAX-AI/1.0)"}
            async with aiohttp.ClientSession() as sess:
                async with sess.get(url, headers=headers,
                                    timeout=aiohttp.ClientTimeout(total=20)) as r:
                    if r.status != 200:
                        return f"HTTP {r.status} for {url}"
                    html = await r.text(errors="replace")
            soup = BeautifulSoup(html, "lxml")
            for tag in soup(["script", "style", "nav", "footer", "aside"]):
                tag.decompose()
            text = soup.get_text(" ", strip=True)
            text = " ".join(text.split())
            return text[:4000] + ("…" if len(text) > 4000 else "")
        except ImportError:
            return "aiohttp or beautifulsoup4 not installed."
        except Exception as e:
            return f"Web fetch error: {e}"


# ─────────────────────────────────────────────
# WEB SEARCH  (DuckDuckGo — no API key)
# ─────────────────────────────────────────────

class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Search the web via DuckDuckGo. Args: query='your question'"
    permission_key = "web_browsing"

    async def run(self, query: str = "", **kwargs) -> str:
        q = query or kwargs.get("input", "")
        if not q:
            return "No search query provided."
        try:
            import aiohttp
            from bs4 import BeautifulSoup
            headers = {"User-Agent": "Mozilla/5.0 (compatible; MAX-AI/1.0)"}
            async with aiohttp.ClientSession() as sess:
                async with sess.post(
                    "https://html.duckduckgo.com/html/",
                    data={"q": q},
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as r:
                    html = await r.text(errors="replace")
            soup = BeautifulSoup(html, "lxml")
            results = []
            for item in soup.select(".result__body")[:5]:
                title = item.select_one(".result__title")
                snippet = item.select_one(".result__snippet")
                link = item.select_one(".result__url")
                t = title.get_text(strip=True) if title else ""
                s = snippet.get_text(strip=True) if snippet else ""
                u = link.get_text(strip=True) if link else ""
                if t:
                    results.append(f"• {t}\n  {s}\n  {u}")
            if results:
                return f"Search: {q}\n\n" + "\n\n".join(results)
            return f"No results for: {q}"
        except Exception as e:
            return f"Search error: {e}"


# ─────────────────────────────────────────────
# FILE READ
# ─────────────────────────────────────────────

class FileReadTool(BaseTool):
    name = "file_read"
    description = "Read a file and return its text content. Args: path='~/path/to/file'"
    permission_key = "file_read"

    async def run(self, path: str = "", **kwargs) -> str:
        p_str = path or kwargs.get("input", "")
        if not p_str:
            return "No file path provided."
        p = Path(os.path.expanduser(p_str))
        if not p.exists():
            return f"File not found: {p_str}"
        if not p.is_file():
            return f"Not a file: {p_str}"
        if p.stat().st_size > 2_000_000:
            return f"File too large (>2 MB): {p_str}"
        try:
            suffix = p.suffix.lower()
            if suffix == ".pdf":
                return await asyncio.to_thread(self._read_pdf, p)
            if suffix == ".docx":
                return await asyncio.to_thread(self._read_docx, p)
            return p.read_text(encoding="utf-8", errors="replace")[:6000]
        except Exception as e:
            return f"Read error: {e}"

    def _read_pdf(self, p: Path) -> str:
        try:
            import PyPDF2
            reader = PyPDF2.PdfReader(str(p))
            pages = [reader.pages[i].extract_text() or "" for i in range(min(10, len(reader.pages)))]
            return "\n".join(pages)[:6000]
        except Exception as e:
            return f"PDF error: {e}"

    def _read_docx(self, p: Path) -> str:
        try:
            from docx import Document
            doc = Document(str(p))
            return "\n".join(para.text for para in doc.paragraphs)[:6000]
        except Exception as e:
            return f"DOCX error: {e}"


# ─────────────────────────────────────────────
# FILE LIST
# ─────────────────────────────────────────────

class FileListTool(BaseTool):
    name = "file_list"
    description = "List files in a directory. Args: path='~/some/folder'"
    permission_key = "file_read"

    async def run(self, path: str = "~", **kwargs) -> str:
        p = Path(os.path.expanduser(path or "~"))
        if not p.exists():
            return f"Path not found: {path}"
        if not p.is_dir():
            return f"Not a directory: {path}"
        try:
            items = sorted(p.iterdir(), key=lambda x: (x.is_file(), x.name))
            lines = []
            for item in items[:50]:
                kind = "DIR " if item.is_dir() else "FILE"
                size = ""
                if item.is_file():
                    s = item.stat().st_size
                    size = f" ({s // 1024} KB)" if s >= 1024 else f" ({s} B)"
                lines.append(f"{kind}  {item.name}{size}")
            if len(list(p.iterdir())) > 50:
                lines.append("... (truncated at 50 items)")
            return f"Contents of {p}:\n" + "\n".join(lines)
        except PermissionError:
            return f"Permission denied: {path}"
        except Exception as e:
            return f"List error: {e}"


# ─────────────────────────────────────────────
# SCREENSHOT
# ─────────────────────────────────────────────

class ScreenshotTool(BaseTool):
    name = "screenshot"
    description = "Take a screenshot of the primary monitor"
    permission_key = "screen_capture"

    async def run(self, **kwargs) -> str:
        out = Path(__file__).parent.parent / "uploads"
        out.mkdir(exist_ok=True)
        fname = out / f"screenshot_{int(time.time())}.png"
        try:
            import mss, mss.tools
            with mss.mss() as sct:
                mon = sct.monitors[1]
                img = sct.grab(mon)
                mss.tools.to_png(img.rgb, img.size, output=str(fname))
            return f"Screenshot saved: {fname}"
        except ImportError:
            pass
        try:
            from PIL import ImageGrab
            img = await asyncio.to_thread(ImageGrab.grab)
            await asyncio.to_thread(img.save, str(fname))
            return f"Screenshot saved: {fname}"
        except Exception as e:
            return f"Screenshot failed: {e}"


# ─────────────────────────────────────────────
# APP LAUNCHER
# ─────────────────────────────────────────────

_APP_MAP = {
    "notepad":     {"win32": "notepad.exe", "darwin": "TextEdit", "linux": "gedit"},
    "calculator":  {"win32": "calc.exe",    "darwin": "Calculator", "linux": "gnome-calculator"},
    "chrome":      {"win32": "chrome",      "darwin": "Google Chrome", "linux": "google-chrome"},
    "firefox":     {"win32": "firefox",     "darwin": "Firefox", "linux": "firefox"},
    "vscode":      {"win32": "code",        "darwin": "code",    "linux": "code"},
    "terminal":    {"win32": "cmd.exe",     "darwin": "Terminal", "linux": "gnome-terminal"},
    "files":       {"win32": "explorer",    "darwin": "Finder",  "linux": "nautilus"},
    "spotify":     {"win32": "spotify",     "darwin": "Spotify", "linux": "spotify"},
    "word":        {"win32": "winword",     "darwin": "Microsoft Word", "linux": "libreoffice --writer"},
    "excel":       {"win32": "excel",       "darwin": "Microsoft Excel", "linux": "libreoffice --calc"},
}


class AppLauncherTool(BaseTool):
    name = "launch_app"
    description = "Launch an application by name. Args: app='chrome'|'vscode'|'terminal'|etc."
    permission_key = "pc_control"
    requires_confirmation = True

    async def run(self, app: str = "", **kwargs) -> str:
        if not app:
            return "No app name provided."
        import subprocess
        plat = sys.platform  # win32 / darwin / linux
        plat_key = "linux" if plat.startswith("linux") else plat

        entry = _APP_MAP.get(app.lower(), {})
        cmd = entry.get(plat_key, app)

        try:
            if sys.platform == "darwin":
                await asyncio.to_thread(
                    subprocess.Popen, ["open", "-a", cmd],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
            else:
                await asyncio.to_thread(
                    subprocess.Popen, cmd, shell=(sys.platform == "win32"),
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
            return f"Launched: {app}"
        except FileNotFoundError:
            return f"App not found: {app} (tried '{cmd}')"
        except Exception as e:
            return f"Launch failed: {e}"


# ─────────────────────────────────────────────
# REGISTRY
# ─────────────────────────────────────────────

class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, BaseTool] = {}
        self._register_defaults()

    def _register_defaults(self):
        for tool in [
            CalculatorTool(),
            DateTimeTool(),
            SystemInfoTool(),
            ClipboardTool(),
            WebFetchTool(),
            WebSearchTool(),
            FileReadTool(),
            FileListTool(),
            ScreenshotTool(),
            AppLauncherTool(),
        ]:
            self._tools[tool.name] = tool
        logger.info(f"Tool registry: {len(self._tools)} tools loaded.")

    def register(self, tool: BaseTool):
        self._tools[tool.name] = tool

    def get(self, name: str):
        return self._tools.get(name)

    def all(self) -> list:
        return list(self._tools.values())

    def names(self) -> list:
        return list(self._tools.keys())
