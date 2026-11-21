"""
MAX AI — Diagnostics Engine
LEREON Technologies

Full system self-check: imports, providers, permissions, storage, voice, vision.
Run via: python main.py --diagnose
"""

import sys
import os
import logging
import time
from pathlib import Path

logger = logging.getLogger("MAX.diagnostics")
ROOT = Path(__file__).parent.parent

PASS = "✅"
WARN = "⚠️ "
FAIL = "❌"
INFO = "ℹ️ "


class Diagnostics:
    def __init__(self):
        self._results: list[dict] = []

    def _add(self, category: str, name: str, status: str, message: str):
        self._results.append({
            "category": category, "name": name,
            "status": status, "message": message
        })

    def run_full_check(self):
        print("\n" + "═" * 65)
        print("  MAX AI — System Diagnostics")
        print("  LEREON Technologies")
        print("═" * 65 + "\n")

        self._check_python()
        self._check_core_imports()
        self._check_optional_imports()
        self._check_config()
        self._check_providers()
        self._check_directories()
        self._check_database()
        self._check_permissions()
        self._check_network()

        # Print results
        categories = {}
        for r in self._results:
            categories.setdefault(r["category"], []).append(r)

        passed = failed = warned = 0
        for cat, items in categories.items():
            print(f"\n  [{cat}]")
            for item in items:
                print(f"  {item['status']}  {item['name']:<35} {item['message']}")
                if PASS in item["status"]:  passed += 1
                elif FAIL in item["status"]: failed += 1
                elif WARN in item["status"]: warned += 1

        print(f"\n{'═' * 65}")
        print(f"  Results: {passed} passed  |  {warned} warnings  |  {failed} failed")

        if failed > 0:
            print(f"\n  ⚠️  Some checks failed. MAX AI may work with reduced functionality.")
        elif warned > 0:
            print(f"\n  ✅  Core checks passed. Some optional features may be unavailable.")
        else:
            print(f"\n  ✅  All checks passed. MAX AI is ready.")
        print("═" * 65 + "\n")

        return failed == 0

    def _check_python(self):
        v = sys.version_info
        ok = (v.major, v.minor) >= (3, 10)
        self._add(
            "Python", f"Python {v.major}.{v.minor}.{v.micro}",
            PASS if ok else FAIL,
            "OK" if ok else "Requires Python 3.10+"
        )

    def _check_core_imports(self):
        core_packages = [
            ("PyQt6",        "PyQt6.QtWidgets"),
            ("openai",       "openai"),
            ("anthropic",    "anthropic"),
            ("aiohttp",      "aiohttp"),
            ("Pillow",       "PIL"),
            ("psutil",       "psutil"),
            ("bs4",          "bs4"),
            ("pyperclip",    "pyperclip"),
            ("pydantic",     "pydantic"),
            ("rich",         "rich"),
        ]
        for display, mod in core_packages:
            try:
                __import__(mod)
                self._add("Core Packages", display, PASS, "Installed")
            except ImportError:
                self._add("Core Packages", display, FAIL, f"Not found — pip install {display}")

    def _check_optional_imports(self):
        optional = [
            ("SpeechRecognition", "speech_recognition", "Voice input (STT)"),
            ("pyttsx3",           "pyttsx3",             "Voice output (TTS)"),
            ("pyaudio",           "pyaudio",             "Microphone access"),
            ("mss",               "mss",                 "Fast screenshots"),
            ("PyPDF2",            "PyPDF2",              "PDF reading"),
            ("python-docx",       "docx",                "Word document reading"),
            ("openai-whisper",    "whisper",             "Local Whisper STT"),
            ("pvporcupine",       "pvporcupine",         "Wake word detection"),
            ("opencv-python",     "cv2",                 "Camera/vision/gesture"),
            ("mediapipe",         "mediapipe",           "Hand gesture control"),
            ("playwright",        "playwright",          "Advanced browser automation"),
            ("pytesseract",       "pytesseract",         "OCR text extraction"),
            ("openpyxl",          "openpyxl",            "Excel file reading"),
            ("google-generativeai","google.generativeai","Gemini provider"),
            ("groq",              "groq",                "Groq provider"),
            ("mistralai",         "mistralai",           "Mistral provider"),
        ]
        for display, mod, purpose in optional:
            try:
                __import__(mod)
                self._add("Optional Packages", display, PASS, purpose)
            except ImportError:
                self._add("Optional Packages", display, WARN, f"Not installed — {purpose}")

    def _check_config(self):
        try:
            sys.path.insert(0, str(ROOT))
            from core.config import Config
            cfg = Config()
            self._add("Configuration", "config.json", PASS, "Loaded OK")

            ep = cfg.enabled_providers
            if ep:
                self._add("Configuration", "AI Providers", PASS, f"Enabled: {', '.join(ep)}")
            else:
                self._add("Configuration", "AI Providers", WARN,
                           "No providers enabled — add API keys to .env or Settings")

            dp = cfg.default_provider
            self._add("Configuration", "Default Provider",
                       PASS if dp else WARN,
                       dp or "Not set — will auto-select")
        except Exception as e:
            self._add("Configuration", "config.json", FAIL, str(e))

    def _check_providers(self):
        """Test that enabled providers can at least initialize."""
        try:
            sys.path.insert(0, str(ROOT))
            from providers.router import ProviderRouter
            router = ProviderRouter()
            statuses = router.status()
            if not statuses:
                self._add("Providers", "Provider Router", WARN, "No providers loaded")
                return
            for s in statuses:
                ok = "ready" in s.get("status", "")
                self._add(
                    "Providers",
                    f"{s['name']} ({s.get('model','')})",
                    PASS if ok else WARN,
                    s.get("status", "unknown")
                )
        except Exception as e:
            self._add("Providers", "Router", FAIL, str(e))

    def _check_directories(self):
        required_dirs = ["config", "logs", "memory", "uploads", "tasks",
                         "plugins/installed"]
        for d in required_dirs:
            p = ROOT / d
            if p.exists():
                self._add("Directories", d, PASS, str(p))
            else:
                try:
                    p.mkdir(parents=True, exist_ok=True)
                    self._add("Directories", d, PASS, f"Created: {p}")
                except Exception as e:
                    self._add("Directories", d, FAIL, str(e))

    def _check_database(self):
        try:
            import sqlite3
            test_db = ROOT / "memory" / "_diag_test.db"
            conn = sqlite3.connect(str(test_db))
            conn.execute("CREATE TABLE IF NOT EXISTS test (id INTEGER)")
            conn.close()
            test_db.unlink(missing_ok=True)
            self._add("Database", "SQLite", PASS, "Read/write OK")
        except Exception as e:
            self._add("Database", "SQLite", FAIL, str(e))

    def _check_permissions(self):
        try:
            from core.config import Config
            cfg = Config()
            perm_map = {
                "web_browsing":   "Web browsing",
                "file_read":      "File read",
                "screen_capture": "Screenshots",
                "microphone":     "Microphone",
                "pc_control":     "PC control",
                "memory":         "Memory persistence",
            }
            for key, label in perm_map.items():
                val = cfg.permission(key)
                self._add("Permissions", label,
                           PASS if val else INFO,
                           "Enabled" if val else "Disabled (can enable in Settings)")
        except Exception as e:
            self._add("Permissions", "Check", FAIL, str(e))

    def _check_network(self):
        import socket
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            self._add("Network", "Internet Connectivity", PASS, "Connected")
        except OSError:
            self._add("Network", "Internet Connectivity", WARN, "No connection — offline mode only")

        # Check Ollama if configured
        try:
            from core.config import Config
            cfg = Config()
            ollama_cfg = cfg.provider_cfg("ollama")
            if ollama_cfg.get("enabled"):
                import urllib.request
                url = ollama_cfg.get("base_url", "http://localhost:11434")
                try:
                    urllib.request.urlopen(f"{url}/api/tags", timeout=2)
                    self._add("Network", "Ollama Local", PASS, f"Reachable at {url}")
                except Exception:
                    self._add("Network", "Ollama Local", WARN, f"Not reachable at {url}")
        except Exception:
            pass
