"""
MAX AI — Ollama Provider (Local + Cloud)
LEREON Technologies

Supports:
  - Local Ollama:  http://localhost:11434  (no auth)
  - Ollama Cloud:  custom URL + Bearer token (api_key)
  - OpenAI-compatible Ollama cloud endpoints (use_openai_compat=True)

Config keys (providers.ollama):
  base_url    - local Ollama URL (default: http://localhost:11434)
  cloud_url   - remote Ollama endpoint (overrides base_url when use_cloud=True)
  api_key     - Bearer token for cloud auth (empty = no auth)
  use_cloud   - bool: use cloud_url instead of base_url
  model       - model name (default: llama3)
"""

import logging
import asyncio
from providers import BaseProvider

logger = logging.getLogger("MAX.providers.ollama")


class OllamaProvider(BaseProvider):
    name = "ollama"

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3",
        cloud_url: str = "",
        api_key: str = "",
        use_cloud: bool = False,
    ):
        self.model = model
        self._local_url  = base_url.rstrip("/")
        self._cloud_url  = cloud_url.rstrip("/") if cloud_url else ""
        self._api_key    = api_key
        self._use_cloud  = use_cloud and bool(cloud_url)

    @property
    def _base_url(self) -> str:
        return self._cloud_url if self._use_cloud else self._local_url

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self._api_key:
            h["Authorization"] = f"Bearer {self._api_key}"
        return h

    async def complete(
        self, messages: list, system: str = "", **kwargs
    ) -> tuple:
        """
        Call Ollama /api/chat (supports full message history).
        Falls back to /api/generate if /api/chat is not available.
        """
        try:
            import aiohttp
        except ImportError:
            raise RuntimeError(
                "aiohttp is required for Ollama: pip install aiohttp"
            )

        # Build message list for /api/chat
        chat_messages = []
        if system:
            chat_messages.append({"role": "system", "content": system})
        for m in messages:
            role = m.get("role", "user")
            if role in ("user", "assistant", "system"):
                chat_messages.append({"role": role, "content": m.get("content", "")})

        payload = {
            "model": self.model,
            "messages": chat_messages,
            "stream": False,
            "options": {
                "num_ctx": kwargs.get("max_tokens", 4096),
            }
        }

        endpoint = f"{self._base_url}/api/chat"
        mode = "cloud" if self._use_cloud else "local"
        logger.debug(f"Ollama {mode} → {endpoint} model={self.model}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    endpoint,
                    json=payload,
                    headers=self._headers(),
                    timeout=aiohttp.ClientTimeout(total=120),
                ) as resp:
                    if resp.status == 404:
                        # Fallback: older Ollama without /api/chat
                        return await self._generate_fallback(session, system, messages, kwargs)
                    if resp.status == 401:
                        raise PermissionError(
                            f"Ollama auth failed (401). Check your api_key in Settings."
                        )
                    if resp.status != 200:
                        body = await resp.text()
                        raise ConnectionError(
                            f"Ollama HTTP {resp.status}: {body[:200]}"
                        )
                    data = await resp.json(content_type=None)

            text = (
                data.get("message", {}).get("content", "")
                or data.get("response", "")
                or ""
            )
            tokens = (
                data.get("prompt_eval_count", 0)
                + data.get("eval_count", 0)
            )
            return text, self.model, tokens

        except aiohttp.ClientConnectorError:
            if self._use_cloud:
                raise ConnectionError(
                    f"Cannot reach Ollama cloud endpoint: {self._base_url}\n"
                    "Check the cloud_url in Settings."
                )
            raise ConnectionError(
                f"Cannot reach local Ollama at {self._base_url}\n"
                "Start Ollama with: ollama serve"
            )

    async def _generate_fallback(
        self, session, system: str, messages: list, kwargs: dict
    ) -> tuple:
        """Fallback to /api/generate for older Ollama versions."""
        parts = []
        if system:
            parts.append(f"System: {system}")
        for m in messages:
            role = m.get("role", "user").capitalize()
            parts.append(f"{role}: {m.get('content', '')}")
        parts.append("Assistant:")
        prompt = "\n\n".join(parts)

        payload = {"model": self.model, "prompt": prompt, "stream": False}

        async with session.post(
            f"{self._base_url}/api/generate",
            json=payload,
            headers=self._headers(),
            timeout=aiohttp.ClientTimeout(total=120),
        ) as resp:
            if resp.status != 200:
                body = await resp.text()
                raise ConnectionError(f"Ollama generate HTTP {resp.status}: {body[:200]}")
            data = await resp.json(content_type=None)

        text = data.get("response", "")
        tokens = data.get("prompt_eval_count", 0) + data.get("eval_count", 0)
        return text, self.model, tokens

    async def list_models(self) -> list:
        """Return list of available models from this Ollama instance."""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self._base_url}/api/tags",
                    headers=self._headers(),
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status != 200:
                        return []
                    data = await resp.json(content_type=None)
                    models = data.get("models", [])
                    return [m.get("name", "") for m in models if m.get("name")]
        except Exception as e:
            logger.warning(f"Ollama list_models failed: {e}")
            return []
