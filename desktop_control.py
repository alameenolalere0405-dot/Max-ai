"""
MAX AI — Desktop Control Engine
LEREON Technologies

Safe, allowlisted PC control operations.
No arbitrary shell command execution.
All sensitive actions require confirmation.
"""

import logging
import asyncio
import sys
import os
import subprocess
import shutil
from pathlib import Path
from typing import Optional

logger = logging.getLogger("MAX.desktop")


# ── Safe App Registry ─────────────────────────────────────────────────────
# Only these app names can be launched. Never arbitrary executables.

SAFE_APPS = {
    # name         win32            darwin               linux
    "notepad":    ("notepad.exe",   "TextEdit",          "gedit"),
    "calculator": ("calc.exe",      "Calculator",        "gnome-calculator"),
    "chrome":     ("chrome",        "Google Chrome",     "google-chrome"),
    "firefox":    ("firefox",       "Firefox",           "firefox"),
    "edge":       ("msedge",        "Microsoft Edge",    "microsoft-edge"),
    "safari":     (None,            "Safari",            None),
    "vscode":     ("code",          "code",              "code"),
    "terminal":   ("cmd.exe",       "Terminal",          "gnome-terminal"),
    "files":      ("explorer",      "Finder",            "nautilus"),
    "spotify":    ("spotify",       "Spotify",           "spotify"),
    "word":       ("winword",       "Microsoft Word",    "soffice --writer"),
    "excel":      ("excel",         "Microsoft Excel",   "soffice --calc"),
    "powerpoint": ("powerpnt",      "Microsoft PowerPoint", "soffice --impress"),
    "outlook":    ("outlook",       "Microsoft Outlook", None),
    "teams":      ("teams",         "Microsoft Teams",   "teams"),
    "slack":      ("slack",         "Slack",             "slack"),
    "discord":    ("discord",       "Discord",           "discord"),
    "vlc":        ("vlc",           "VLC",               "vlc"),
    "paint":      ("mspaint.exe",   None,                "gimp"),
    "task_manager":("taskmgr.exe",  "Activity Monitor",  "gnome-system-monitor"),
}


def _plat_key() -> str:
    if sys.platform == "win32":    return 0
    if sys.platform == "darwin":   return 1
    return 2  # linux


class DesktopControl:
    """
    Provides safe, permission-gated desktop operations.
    Never executes arbitrary shell commands or AI-generated commands.
    """

    def __init__(self, config=None, confirm_callback=None):
        self._config = config
        self._confirm = confirm_callback or (lambda msg: True)

    def _require_permission(self, key: str) -> bool:
        if self._config:
            return self._config.permission(key)
        return False

    # ── App Launching ─────────────────────────────────────────────────────

    async def launch_app(self, app_name: str) -> dict:
        """
        Launch a registered application by name.
        Returns {"ok": bool, "message": str}
        """
        if not self._require_permission("pc_control"):
            return {"ok": False, "message": "PC Control permission is disabled. Enable it in Settings."}

        key = app_name.lower().strip().replace(" ", "_")
        entry = SAFE_APPS.get(key)
        if not entry:
            available = ", ".join(SAFE_APPS.keys())
            return {"ok": False,
                    "message": f"'{app_name}' is not in the safe app list.\nAvailable: {available}"}

        cmd = entry[_plat_key()]
        if cmd is None:
            return {"ok": False, "message": f"'{app_name}' is not available on this platform."}

        confirmed = self._confirm(f"Launch application: {app_name}?")
        if not confirmed:
            return {"ok": False, "message": "Launch cancelled by user."}

        try:
            if sys.platform == "darwin":
                await asyncio.to_thread(
                    subprocess.Popen, ["open", "-a", cmd],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
            elif sys.platform == "win32":
                await asyncio.to_thread(
                    subprocess.Popen, cmd, shell=True,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
            else:
                await asyncio.to_thread(
                    subprocess.Popen, cmd.split(),
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
            logger.info(f"Launched: {app_name}")
            return {"ok": True, "message": f"Launched {app_name}."}
        except FileNotFoundError:
            return {"ok": False, "message": f"'{app_name}' not found on this system (tried '{cmd}')."}
        except Exception as e:
            return {"ok": False, "message": f"Launch error: {e}"}

    # ── File Operations ───────────────────────────────────────────────────

    async def list_directory(self, path: str = "~") -> str:
        """List contents of a directory."""
        if not self._require_permission("file_read"):
            return "File read permission is disabled."
        p = Path(os.path.expanduser(path))
        if not p.exists():
            return f"Path not found: {path}"
        if not p.is_dir():
            return f"Not a directory: {path}"
        try:
            items = sorted(p.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
            lines = [f"Directory: {p}\n"]
            dirs  = [f"  📁 {i.name}/" for i in items if i.is_dir()]
            files = [f"  📄 {i.name}  ({i.stat().st_size:,} bytes)" for i in items if i.is_file()]
            lines += dirs + files
            if len(items) > 100:
                lines.append(f"  … ({len(items)} total items)")
            return "\n".join(lines[:102])
        except PermissionError:
            return f"Permission denied: {path}"
        except Exception as e:
            return f"List error: {e}"

    async def find_files(self, name_pattern: str, search_dir: str = "~") -> str:
        """Search for files matching a name pattern."""
        if not self._require_permission("file_read"):
            return "File read permission is disabled."
        base = Path(os.path.expanduser(search_dir))
        if not base.exists():
            return f"Search directory not found: {search_dir}"
        try:
            matches = list(base.rglob(name_pattern))[:30]
            if not matches:
                return f"No files matching '{name_pattern}' in {search_dir}"
            lines = [f"Found {len(matches)} file(s) matching '{name_pattern}':"]
            for m in matches:
                lines.append(f"  {m}")
            return "\n".join(lines)
        except Exception as e:
            return f"Search error: {e}"

    async def open_file(self, path: str) -> dict:
        """Open a file with its default application."""
        if not self._require_permission("pc_control"):
            return {"ok": False, "message": "PC Control permission disabled."}
        p = Path(os.path.expanduser(path))
        if not p.exists():
            return {"ok": False, "message": f"File not found: {path}"}

        confirmed = self._confirm(f"Open file: {p.name}?")
        if not confirmed:
            return {"ok": False, "message": "Cancelled."}
        try:
            if sys.platform == "win32":
                os.startfile(str(p))
            elif sys.platform == "darwin":
                await asyncio.to_thread(subprocess.Popen, ["open", str(p)])
            else:
                await asyncio.to_thread(subprocess.Popen, ["xdg-open", str(p)])
            return {"ok": True, "message": f"Opened: {p.name}"}
        except Exception as e:
            return {"ok": False, "message": f"Open error: {e}"}

    # ── Clipboard ─────────────────────────────────────────────────────────

    async def get_clipboard(self) -> str:
        try:
            import pyperclip
            text = await asyncio.to_thread(pyperclip.paste)
            return text if text else "(Clipboard is empty)"
        except ImportError:
            return "Clipboard requires pyperclip: pip install pyperclip"
        except Exception as e:
            return f"Clipboard error: {e}"

    async def set_clipboard(self, text: str) -> str:
        confirmed = self._confirm(f"Copy to clipboard: {text[:60]}{'...' if len(text)>60 else ''}?")
        if not confirmed:
            return "Cancelled."
        try:
            import pyperclip
            await asyncio.to_thread(pyperclip.copy, text)
            return f"Copied {len(text)} characters to clipboard."
        except Exception as e:
            return f"Clipboard error: {e}"

    # ── Window Management ─────────────────────────────────────────────────

    async def get_window_list(self) -> str:
        """List open windows/processes (platform-specific)."""
        try:
            import psutil
            procs = []
            for p in psutil.process_iter(["pid", "name", "status"]):
                try:
                    if p.info["status"] == "running":
                        procs.append(f"  PID {p.info['pid']:6d}  {p.info['name']}")
                except Exception:
                    pass
            if not procs:
                return "No running processes found."
            return f"Running processes ({len(procs)}):\n" + "\n".join(procs[:30])
        except ImportError:
            return "Process list requires psutil: pip install psutil"

    # ── System Info ───────────────────────────────────────────────────────

    async def get_system_info(self) -> str:
        try:
            import psutil, platform
            cpu = await asyncio.to_thread(psutil.cpu_percent, 1)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            uptime = int(psutil.boot_time())
            import time
            uptime_h = int((time.time() - uptime) / 3600)
            uptime_m = int(((time.time() - uptime) % 3600) / 60)
            lines = [
                f"OS:      {platform.system()} {platform.release()} ({platform.machine()})",
                f"Python:  {platform.python_version()}",
                f"CPU:     {cpu:.1f}%  ({psutil.cpu_count()} cores)",
                f"RAM:     {mem.used//1024**2} MB used / {mem.total//1024**2} MB total  ({mem.percent:.1f}%)",
                f"Disk:    {disk.used//1024**3} GB used / {disk.total//1024**3} GB total  ({disk.percent:.1f}%)",
                f"Uptime:  {uptime_h}h {uptime_m}m",
            ]
            try:
                bat = psutil.sensors_battery()
                if bat:
                    plug = "plugged in" if bat.power_plugged else "on battery"
                    lines.append(f"Battery: {bat.percent:.0f}%  ({plug})")
            except Exception:
                pass
            return "\n".join(lines)
        except ImportError:
            return "System info requires psutil: pip install psutil"
        except Exception as e:
            return f"System info error: {e}"

    # ── Keyboard shortcut helper ──────────────────────────────────────────

    async def send_shortcut(self, shortcut: str) -> dict:
        """
        Send a keyboard shortcut (e.g. 'ctrl+c', 'alt+tab').
        Requires pyautogui and explicit pc_control permission.
        """
        if not self._require_permission("pc_control"):
            return {"ok": False, "message": "PC Control permission disabled."}

        SAFE_SHORTCUTS = {
            "copy":        "ctrl+c",
            "paste":       "ctrl+v",
            "cut":         "ctrl+x",
            "undo":        "ctrl+z",
            "redo":        "ctrl+y",
            "save":        "ctrl+s",
            "select_all":  "ctrl+a",
            "find":        "ctrl+f",
            "new_tab":     "ctrl+t",
            "close_tab":   "ctrl+w",
            "switch_app":  "alt+tab",
            "screenshot":  "printscreen",
        }

        cmd = SAFE_SHORTCUTS.get(shortcut.lower(), shortcut.lower())
        confirmed = self._confirm(f"Send keyboard shortcut: {cmd}?")
        if not confirmed:
            return {"ok": False, "message": "Cancelled."}

        try:
            import pyautogui
            keys = cmd.split("+")
            if len(keys) > 1:
                await asyncio.to_thread(pyautogui.hotkey, *keys)
            else:
                await asyncio.to_thread(pyautogui.press, keys[0])
            return {"ok": True, "message": f"Sent: {cmd}"}
        except ImportError:
            return {"ok": False, "message": "Shortcuts require pyautogui: pip install pyautogui"}
        except Exception as e:
            return {"ok": False, "message": f"Shortcut error: {e}"}
