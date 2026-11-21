"""MAX AI — Mistral Provider"""

import logging
import asyncio
from providers import BaseProvider

logger = logging.getLogger("MAX.providers.mistral")


class MistralProvider(BaseProvider):
    name = "mistral"

    def __init__(self, api_key: str, model: str = "mistral-large-latest"):
        self.model = model
        self._api_key = api_key
        self._client = None

    def _client_obj(self):
        if self._client is None:
            from mistralai import Mistral
            self._client = Mistral(api_key=self._api_key)
        return self._client

    async def complete(self, messages: list, system: str = "", **kwargs) -> tuple:
        client = self._client_obj()
        full = []
        if system:
            full.append({"role": "system", "content": system})
        full.extend(messages)
        resp = await asyncio.to_thread(
            client.chat.complete,
            model=self.model,
            messages=full,
        )
        text = resp.choices[0].message.content or ""
        tokens = resp.usage.total_tokens if resp.usage else 0
        return text, self.model, tokens
