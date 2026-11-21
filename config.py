"""MAX AI — Configuration Manager"""

import json
import os
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("MAX.config")
ROOT = Path(__file__).parent.parent


def _load_env_file():
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v


class Config:
    def __init__(self):
        _load_env_file()
        self._data: dict = {}
        self.reload()

    def reload(self):
        path = ROOT / "config" / "config.json"
        if path.exists():
            with open(path, encoding="utf-8") as f:
                self._data = json.load(f)
        else:
            self._data = {}
        self._inject_env()

    def _inject_env(self):
        env_map = {
            "OPENAI_API_KEY":       ("providers", "openai",     "api_key"),
            "ANTHROPIC_API_KEY":    ("providers", "anthropic",  "api_key"),
            "GOOGLE_API_KEY":       ("providers", "gemini",     "api_key"),
            "GROQ_API_KEY":         ("providers", "groq",       "api_key"),
            "DEEPSEEK_API_KEY":     ("providers", "deepseek",   "api_key"),
            "MISTRAL_API_KEY":      ("providers", "mistral",    "api_key"),
            "OPENROUTER_API_KEY":   ("providers", "openrouter", "api_key"),
            "OLLAMA_BASE_URL":      ("providers", "ollama",     "base_url"),
        }
        for env_var, (section, provider, field) in env_map.items():
            val = os.environ.get(env_var, "").strip()
            if val:
                if section not in self._data:
                    self._data[section] = {}
                if provider not in self._data[section]:
                    self._data[section][provider] = {}
                self._data[section][provider][field] = val
                if field == "api_key":
                    self._data[section][provider]["enabled"] = True

        # Auto-select default provider
        if not self._data.get("providers", {}).get("default"):
            for name in self._data.get("providers", {}).get("fallback_order", []):
                p = self._data.get("providers", {}).get(name, {})
                if p.get("enabled") and (p.get("api_key") or name == "ollama"):
                    self._data["providers"]["default"] = name
                    break

    def save(self):
        path = ROOT / "config" / "config.json"
        path.parent.mkdir(exist_ok=True)
        import copy
        safe = copy.deepcopy(self._data)
        # Strip API keys from config.json — they live in .env
        # But preserve all other provider config (models, urls, cloud settings)
        for pname, p in safe.get("providers", {}).items():
            if isinstance(p, dict) and p.get("api_key"):
                p["api_key"] = ""   # never write keys to config.json
        # Remove internal test keys
        safe.pop("test_persist", None)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(safe, f, indent=2)

    def get(self, *keys, default=None) -> Any:
        d = self._data
        for k in keys:
            if not isinstance(d, dict):
                return default
            d = d.get(k)
            if d is None:
                return default
        return d if d is not None else default

    def set(self, *args):
        """set('section', 'key', value)"""
        *keys, value = args
        d = self._data
        for k in keys[:-1]:
            d = d.setdefault(k, {})
        d[keys[-1]] = value

    # ── Shortcuts ──────────────────────────────────────────────────────

    @property
    def default_provider(self) -> str:
        return self.get("providers", "default", default="")

    @property
    def enabled_providers(self) -> list:
        result = []
        skip = {"default", "fallback_order"}
        for name, cfg in self._data.get("providers", {}).items():
            if name in skip:
                continue
            if isinstance(cfg, dict) and cfg.get("enabled"):
                result.append(name)
        return result

    def provider_cfg(self, name: str) -> dict:
        return self.get("providers", name, default={})

    def permission(self, key: str) -> bool:
        return bool(self.get("permissions", key, default=False))

    @property
    def memory_enabled(self) -> bool:
        return bool(self.get("memory", "enabled", default=True))

    @property
    def voice_input_enabled(self) -> bool:
        return bool(self.get("assistant", "voice_input_enabled", default=False))

    @property
    def voice_output_enabled(self) -> bool:
        return bool(self.get("assistant", "voice_output_enabled", default=False))

    @property
    def wake_word_enabled(self) -> bool:
        return bool(self.get("assistant", "wake_word_enabled", default=False))

    @property
    def assistant_name(self) -> str:
        return self.get("assistant", "name", default="MAX")


_config = None


def get_config() -> Config:
    global _config
    if _config is None:
        _config = Config()
    return _config
