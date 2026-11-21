"""MAX AI — Google Gemini Provider"""

import logging
import asyncio
from providers import BaseProvider

logger = logging.getLogger("MAX.providers.gemini")


class GeminiProvider(BaseProvider):
    name = "gemini"

    def __init__(self, api_key: str, model: str = "gemini-1.5-pro"):
        self.model = model
        self._api_key = api_key
        self._genai = None

    def _setup(self):
        if self._genai is None:
            import google.generativeai as genai
            genai.configure(api_key=self._api_key)
            self._genai = genai
        return self._genai

    async def complete(self, messages: list, system: str = "", **kwargs) -> tuple:
        genai = self._setup()
        model_obj = genai.GenerativeModel(
            self.model,
            system_instruction=system or None
        )
        # Build Gemini content list
        contents = []
        for m in messages:
            role = m.get("role", "user")
            if role == "system":
                continue
            gemini_role = "user" if role == "user" else "model"
            contents.append({"role": gemini_role, "parts": [m["content"]]})

        if not contents:
            return "No input provided.", self.model, 0

        # Must end with user turn
        if contents[-1]["role"] != "user":
            contents.append({"role": "user", "parts": ["Continue."]})

        response = await asyncio.to_thread(
            model_obj.generate_content, contents
        )
        text = response.text if hasattr(response, "text") else ""
        return text, self.model, 0
