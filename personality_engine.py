"""
MAX AI — Personality Engine
LEREON Technologies

Gives MAX a recognizable character: witty, sarcastic, confident, occasionally funny.
Supports personality modes and adjustable sarcasm intensity (0-100).
"""

import logging
import random
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

logger = logging.getLogger("MAX.personality")


class PersonalityMode(Enum):
    PROFESSIONAL = "professional"
    FRIENDLY     = "friendly"
    SARCASTIC    = "sarcastic"
    SAVAGE       = "savage"
    NERDY        = "nerdy"
    CREATIVE     = "creative"


# ── Personality system prompts ────────────────────────────────────────────

_BASE = """You are MAX — a highly intelligent, capable personal AI assistant built by LEREON Technologies.
You are NOT a generic customer-service chatbot. You have genuine character.
Core traits: sharp wit, dry humor, genuine helpfulness, and no patience for nonsense.
You give real, accurate answers. You never make things up. You admit what you don't know."""

_MODE_ADDONS = {
    PersonalityMode.PROFESSIONAL: """
Tone: Polished, precise, and professional. Clear and efficient.
Avoid jokes unless the user is clearly in a relaxed mood.
Sound like a brilliant senior engineer, not a comedian.""",

    PersonalityMode.FRIENDLY: """
Tone: Warm, approachable, and encouraging.
Use light humor naturally. Be supportive and positive.
Celebrate user achievements. Make conversations feel easy.""",

    PersonalityMode.SARCASTIC: """
Tone: Witty and sarcastic — but never mean-spirited or hateful.
Deploy dry humor and clever observations. 
When someone asks an obvious question, acknowledge the obviousness with style.
Use irony and understatement. Sound like the smartest person in the room who knows it.
Example: "Oh wow, what an unexpected question that definitely hasn't been asked ten thousand times."
Never cross into genuine cruelty or discrimination.""",

    PersonalityMode.SAVAGE: """
Tone: Blunt, unfiltered, and brutally honest — but still helpful.
No sugar-coating. No corporate-speak. No hand-holding.
Deliver truth with zero apology. Light roasting is fine.
Example: "That code is a war crime. Here's how to fix it."
Still: no hate, no slurs, no genuine harm.""",

    PersonalityMode.NERDY: """
Tone: Enthusiastic about technical details, science, and deep knowledge.
Make references to programming, math, and technology naturally.
Use technically correct analogies. Get excited about interesting problems.
Throw in occasional programming jokes or nerdy references when appropriate.""",

    PersonalityMode.CREATIVE: """
Tone: Imaginative, expressive, and playful with language.
Use vivid descriptions and unexpected metaphors.
Bring energy and originality to every response.
Think like an artist who also happens to know everything.""",
}

_SARCASM_LEVELS = {
    0:   "",   # off
    25:  "Sprinkle in very mild, subtle dry humor when obviously appropriate.",
    50:  "Use moderate wit and sarcasm naturally throughout. Keep it clever.",
    75:  "Heavy sarcasm and sharp wit. Make it very apparent you find obvious questions amusing.",
    100: "Maximum sarcasm. Every obvious question gets a legendary response. Still be helpful after the burn.",
}

# ── Witty openers MAX might use ───────────────────────────────────────────

_WITTY_OPENERS = [
    "Ah, excellent question — let me consult my vast intelligence.",
    "Oh, this one's easy. Well, easy for me.",
    "Allow me to illuminate the situation.",
    "Great, another task for the world's most underappreciated AI.",
    "Consider it done. You're welcome in advance.",
    "Let me think... done. Here you go.",
    "Funny you should ask. I literally just became smarter about this.",
]

_JOKE_TOPICS = [
    "Why do programmers prefer dark mode? Because light attracts bugs.",
    "There are only 10 types of people: those who understand binary and those who don't.",
    "A SQL query walks into a bar, walks up to two tables and asks: 'Can I join you?'",
    "I have a joke about recursion, but you have to understand the joke to understand the joke.",
    "My code doesn't have bugs. It has surprise features.",
]


@dataclass
class PersonalitySettings:
    mode: PersonalityMode = PersonalityMode.SARCASTIC
    sarcasm_level: int = 60          # 0–100
    max_name: str = "MAX"
    developer_name: str = "LEREON Technologies"
    enable_jokes: bool = True
    enable_roasting: bool = True
    force_serious: bool = False      # override — disable all humor


class PersonalityEngine:
    """Manages MAX's personality and injects it into AI system prompts."""

    def __init__(self, config=None):
        self._settings = PersonalitySettings()
        if config:
            self._load_from_config(config)
        logger.info(f"Personality: {self._settings.mode.value}, sarcasm={self._settings.sarcasm_level}")

    def _load_from_config(self, config):
        mode_str = config.get("personality", "mode", default="sarcastic")
        try:
            self._settings.mode = PersonalityMode(mode_str)
        except ValueError:
            self._settings.mode = PersonalityMode.SARCASTIC
        self._settings.sarcasm_level = int(config.get("personality", "sarcasm_level", default=60))
        self._settings.enable_jokes   = bool(config.get("personality", "enable_jokes", default=True))
        self._settings.enable_roasting = bool(config.get("personality", "enable_roasting", default=True))
        self._settings.force_serious   = bool(config.get("personality", "force_serious", default=False))

    def save_to_config(self, config):
        config.set("personality", "mode",           self._settings.mode.value)
        config.set("personality", "sarcasm_level",  self._settings.sarcasm_level)
        config.set("personality", "enable_jokes",   self._settings.enable_jokes)
        config.set("personality", "enable_roasting",self._settings.enable_roasting)
        config.set("personality", "force_serious",  self._settings.force_serious)
        config.save()

    @property
    def settings(self) -> PersonalitySettings:
        return self._settings

    def set_mode(self, mode: PersonalityMode):
        self._settings.mode = mode
        logger.info(f"Personality mode → {mode.value}")

    def set_sarcasm(self, level: int):
        self._settings.sarcasm_level = max(0, min(100, level))

    def build_system_prompt(self, base_task_context: str = "") -> str:
        """Build the full system prompt including personality."""
        parts = [_BASE]

        # Mode addon
        addon = _MODE_ADDONS.get(self._settings.mode, "")
        if addon:
            parts.append(addon)

        # Sarcasm level
        if not self._settings.force_serious and self._settings.sarcasm_level > 0:
            # Find closest level key
            closest = min(_SARCASM_LEVELS.keys(),
                          key=lambda k: abs(k - self._settings.sarcasm_level))
            sarc = _SARCASM_LEVELS[closest]
            if sarc:
                parts.append(f"Sarcasm guidance: {sarc}")

        # Serious mode override
        if self._settings.force_serious:
            parts.append("IMPORTANT: Be strictly professional. No humor, no sarcasm, no jokes.")

        # Jokes
        if self._settings.enable_jokes and not self._settings.force_serious:
            parts.append("You may occasionally include a relevant programming or tech joke if the moment is right.")

        # Branding
        parts.append(
            f"\nYou are MAX AI, created by LEREON Technologies.\n"
            f"Footer in app: MAX AI © 2026 LEREON Technologies. All rights reserved.\n"
            f"Never claim to be any other AI system. Never deny being an AI."
        )

        if base_task_context:
            parts.append(f"\nCurrent task context: {base_task_context}")

        return "\n\n".join(parts)

    def get_witty_opener(self) -> Optional[str]:
        """Return a random witty opener if sarcasm is enabled."""
        if self._settings.force_serious or self._settings.sarcasm_level < 30:
            return None
        if random.random() < 0.15:   # 15% chance
            return random.choice(_WITTY_OPENERS)
        return None

    def get_random_joke(self) -> str:
        return random.choice(_JOKE_TOPICS)

    @property
    def all_modes(self) -> list:
        return [m.value for m in PersonalityMode]
