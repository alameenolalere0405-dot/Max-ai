"""
MAX AI — Anthropic Claude Provider
LEREON Technologies — Streaming supported
"""
import logging
from typing import AsyncGenerator
from providers import BaseProvider

logger = logging.getLogger("MAX.providers.anthropic")


class AnthropicProvider(BaseProvider):
    name = "anthropic"

    def __init__(self, api_key: str, model: str = "claude-opus-4-5"):
        self.model = model
        self._api_key = api_key
        self._client = None

    def _client_obj(self):
        if self._client is None:
            import anthropic
            self._client = anthropic.AsyncAnthropic(api_key=self._api_key)
        return self._client

    async def complete(self, messages: list, system: str = "", **kwargs) -> tuple:
        client = self._client_obj()
        filtered = [m for m in messages if m.get("role") in ("user", "assistant")]
        sys_extras = [m["content"] for m in messages if m.get("role") == "system"]
        if sys_extras:
            system = (system + "\n\n" + "\n\n".join(sys_extras)).strip()
        resp = await client.messages.create(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 4096),
            system=system or "You are MAX, a helpful AI assistant by LEREON Technologies.",
            messages=filtered,
        )
        text = resp.content[0].text if resp.content else ""
        tokens = (resp.usage.input_tokens or 0) + (resp.usage.output_tokens or 0)
        return text, self.model, tokens

    async def stream(self, messages: list, system: str = "",
                     **kwargs) -> AsyncGenerator[str, None]:
        """Yield text chunks as they stream from Claude."""
        client = self._client_obj()
        filtered = [m for m in messages if m.get("role") in ("user", "assistant")]
        sys_extras = [m["content"] for m in messages if m.get("role") == "system"]
        if sys_extras:
            system = (system + "\n\n" + "\n\n".join(sys_extras)).strip()

        async with client.messages.stream(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 4096),
            system=system or "You are MAX, a helpful AI assistant by LEREON Technologies.",
            messages=filtered,
        ) as stream:
            async for text in stream.text_stream:
                if text:
                    yield text

    async def list_models(self) -> list:
        return [
            "claude-opus-4-5", "claude-sonnet-4-5",
            "claude-haiku-4-5", "claude-3-5-sonnet-latest",
        ]
