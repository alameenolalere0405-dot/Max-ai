"""
MAX AI — OpenAI Provider (also DeepSeek, OpenRouter)
LEREON Technologies — Streaming supported
"""
import logging
from typing import AsyncGenerator, Optional
from providers import BaseProvider

logger = logging.getLogger("MAX.providers.openai")


class OpenAIProvider(BaseProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o",
                 base_url: str = None, name: str = "openai"):
        self.name = name
        self.model = model
        self._api_key = api_key
        self._base_url = base_url
        self._client = None

    def _client_obj(self):
        if self._client is None:
            from openai import AsyncOpenAI
            kw = {"api_key": self._api_key}
            if self._base_url:
                kw["base_url"] = self._base_url
            self._client = AsyncOpenAI(**kw)
        return self._client

    async def complete(self, messages: list, system: str = "", **kwargs) -> tuple:
        client = self._client_obj()
        full = []
        if system:
            full.append({"role": "system", "content": system})
        full.extend(messages)
        resp = await client.chat.completions.create(
            model=self.model,
            messages=full,
            max_tokens=kwargs.get("max_tokens", 4096),
            temperature=kwargs.get("temperature", 0.7),
        )
        text = resp.choices[0].message.content or ""
        tokens = resp.usage.total_tokens if resp.usage else 0
        return text, self.model, tokens

    async def stream(self, messages: list, system: str = "",
                     **kwargs) -> AsyncGenerator[str, None]:
        """Yield response text chunks as they arrive."""
        client = self._client_obj()
        full = []
        if system:
            full.append({"role": "system", "content": system})
        full.extend(messages)
        async with client.chat.completions.stream(
            model=self.model,
            messages=full,
            max_tokens=kwargs.get("max_tokens", 4096),
            temperature=kwargs.get("temperature", 0.7),
        ) as stream:
            async for chunk in stream:
                delta = chunk.choices[0].delta.content if chunk.choices else None
                if delta:
                    yield delta

    async def list_models(self) -> list:
        try:
            client = self._client_obj()
            resp = await client.models.list()
            return [m.id for m in resp.data if "gpt" in m.id or "o1" in m.id or "o3" in m.id]
        except Exception:
            return []
