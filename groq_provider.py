"""MAX AI — Groq Provider — LEREON Technologies — Streaming supported"""
import logging
from typing import AsyncGenerator
from providers import BaseProvider

logger = logging.getLogger("MAX.providers.groq")

class GroqProvider(BaseProvider):
    name = "groq"
    def __init__(self, api_key: str, model: str = "llama3-70b-8192"):
        self.model = model
        self._api_key = api_key
        self._client = None

    def _client_obj(self):
        if self._client is None:
            from groq import AsyncGroq
            self._client = AsyncGroq(api_key=self._api_key)
        return self._client

    async def complete(self, messages: list, system: str = "", **kwargs) -> tuple:
        client = self._client_obj()
        full = []
        if system:
            full.append({"role": "system", "content": system})
        full.extend(messages)
        resp = await client.chat.completions.create(
            model=self.model, messages=full,
            max_tokens=kwargs.get("max_tokens", 4096),
        )
        text = resp.choices[0].message.content or ""
        tokens = resp.usage.total_tokens if resp.usage else 0
        return text, self.model, tokens

    async def stream(self, messages: list, system: str = "",
                     **kwargs) -> AsyncGenerator[str, None]:
        client = self._client_obj()
        full = []
        if system:
            full.append({"role": "system", "content": system})
        full.extend(messages)
        resp = await client.chat.completions.create(
            model=self.model, messages=full,
            max_tokens=kwargs.get("max_tokens", 4096), stream=True,
        )
        async for chunk in resp:
            delta = chunk.choices[0].delta.content if chunk.choices else None
            if delta:
                yield delta

    async def list_models(self) -> list:
        try:
            client = self._client_obj()
            resp = await client.models.list()
            return [m.id for m in resp.data]
        except Exception:
            return ["llama3-70b-8192", "mixtral-8x7b-32768", "gemma2-9b-it"]
