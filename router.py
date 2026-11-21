"""MAX AI — Dynamic Provider Router"""

import logging
from typing import Optional
from core.config import get_config

logger = logging.getLogger("MAX.router")


class ProviderRouter:
    def __init__(self):
        self.config = get_config()
        self._providers: dict = {}
        self._errors: dict = {}
        self._discover()

    def _discover(self):
        loaders = {
            "openai":     self._load_openai,
            "anthropic":  self._load_anthropic,
            "gemini":     self._load_gemini,
            "groq":       self._load_groq,
            "deepseek":   self._load_deepseek,
            "mistral":    self._load_mistral,
            "openrouter": self._load_openrouter,
            "ollama":     self._load_ollama,
        }
        for name, loader in loaders.items():
            cfg = self.config.provider_cfg(name)
            if not cfg.get("enabled"):
                continue
            try:
                self._providers[name] = loader(cfg)
                logger.info(f"Provider ready: {name} ({cfg.get('model', '')})")
            except Exception as e:
                self._errors[name] = str(e)
                logger.warning(f"Provider {name} failed: {e}")

        if not self._providers:
            logger.warning("No providers loaded — check API keys in .env or settings.")

    def _load_openai(self, cfg):
        from providers.openai_provider import OpenAIProvider
        return OpenAIProvider(api_key=cfg["api_key"], model=cfg.get("model", "gpt-4o"))

    def _load_anthropic(self, cfg):
        from providers.anthropic_provider import AnthropicProvider
        return AnthropicProvider(api_key=cfg["api_key"], model=cfg.get("model", "claude-opus-4-5"))

    def _load_gemini(self, cfg):
        from providers.gemini_provider import GeminiProvider
        return GeminiProvider(api_key=cfg["api_key"], model=cfg.get("model", "gemini-1.5-pro"))

    def _load_groq(self, cfg):
        from providers.groq_provider import GroqProvider
        return GroqProvider(api_key=cfg["api_key"], model=cfg.get("model", "llama3-70b-8192"))

    def _load_deepseek(self, cfg):
        from providers.openai_provider import OpenAIProvider
        return OpenAIProvider(
            api_key=cfg["api_key"],
            model=cfg.get("model", "deepseek-chat"),
            base_url="https://api.deepseek.com/v1",
            name="deepseek"
        )

    def _load_mistral(self, cfg):
        from providers.mistral_provider import MistralProvider
        return MistralProvider(api_key=cfg["api_key"], model=cfg.get("model", "mistral-large-latest"))

    def _load_openrouter(self, cfg):
        from providers.openai_provider import OpenAIProvider
        return OpenAIProvider(
            api_key=cfg["api_key"],
            model=cfg.get("model", "openai/gpt-4o"),
            base_url="https://openrouter.ai/api/v1",
            name="openrouter"
        )

    def _load_ollama(self, cfg):
        from providers.ollama_provider import OllamaProvider
        return OllamaProvider(
            base_url=cfg.get("base_url", "http://localhost:11434"),
            model=cfg.get("model", "llama3"),
            cloud_url=cfg.get("cloud_url", ""),
            api_key=cfg.get("api_key", ""),
            use_cloud=bool(cfg.get("use_cloud", False)),
        )

    def get(self, name: str):
        p = self._providers.get(name)
        if p is None:
            raise ValueError(f"Provider '{name}' not available. Error: {self._errors.get(name, 'not configured')}")
        return p

    def get_fallback(self, exclude: list = None):
        exclude = set(exclude or [])
        order = self.config.get("providers", "fallback_order", default=[])
        for name in order:
            if name not in exclude and name in self._providers:
                logger.info(f"Using fallback provider: {name}")
                return self._providers[name]
        return None

    def reload(self):
        self._providers.clear()
        self._errors.clear()
        self.config.reload()
        self._discover()

    @property
    def has_any(self) -> bool:
        return bool(self._providers)

    def status(self) -> list:
        result = []
        for name, p in self._providers.items():
            result.append({"name": name, "model": p.model, "status": "ready"})
        for name, err in self._errors.items():
            result.append({"name": name, "model": "", "status": f"error: {err[:60]}"})
        return result
