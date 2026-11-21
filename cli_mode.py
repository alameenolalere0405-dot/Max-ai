"""
MAX AI — CLI Mode
LEREON Technologies

Full-featured terminal interface when PyQt6 is unavailable or --cli is used.
"""

import sys
import logging
from typing import Optional

logger = logging.getLogger("MAX.cli")


class CLIMode:
    """Interactive terminal chat with MAX AI."""

    BANNER = """
╔══════════════════════════════════════════════════════╗
║          MAX AI — Modular Autonomous eXecutive       ║
║          LEREON Technologies                         ║
╠══════════════════════════════════════════════════════╣
║  Commands:  exit/quit · clear · status · help        ║
║             tools · memory · joke · /tool <name>     ║
╚══════════════════════════════════════════════════════╝
"""

    def __init__(self, force_provider: Optional[str] = None, start_voice: bool = False):
        self._force_provider = force_provider
        self._start_voice = start_voice
        self._core = None

    def _boot(self):
        try:
            from core.max_core import MAXCore
            self._core = MAXCore()
            logger.info("MAX Core ready for CLI.")
        except Exception as e:
            print(f"[ERROR] Failed to boot MAX Core: {e}")
            sys.exit(1)

    def run(self):
        self._boot()
        print(self.BANNER)
        prov = self._core.config.default_provider or "none"
        mode = self._core.personality.settings.mode.value
        print(f"  Provider: {prov}  |  Personality: {mode}")
        print(f"  Enabled providers: {', '.join(self._core.config.enabled_providers) or 'none'}\n")

        while True:
            try:
                user_input = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nMAX: Goodbye. — LEREON Technologies")
                break

            if not user_input:
                continue

            cmd = user_input.lower()

            if cmd in ("exit", "quit", "bye", "goodbye"):
                print("MAX: Shutting down. Stay legendary.")
                break

            if cmd == "clear":
                self._core.clear_conversation()
                print("  [Conversation cleared]")
                continue

            if cmd == "status":
                s = self._core.status()
                for k, v in s.items():
                    print(f"  {k}: {v}")
                continue

            if cmd == "tools":
                names = self._core.tools.names()
                print(f"  Available tools ({len(names)}): {', '.join(names)}")
                continue

            if cmd == "memory":
                hist = self._core.memory.get_history(10)
                if not hist:
                    print("  [Memory is empty]")
                else:
                    print(f"  Last {len(hist)} exchanges:")
                    for h in hist[-5:]:
                        print(f"    You: {h['user'][:60]}")
                        print(f"    MAX: {h['assistant'][:80]}")
                continue

            if cmd == "joke":
                joke = self._core.personality.get_random_joke()
                print(f"MAX: {joke}\n")
                continue

            if cmd == "help":
                print("""
  Commands:
    exit/quit    — Shut down MAX AI
    clear        — Clear conversation history
    status       — Show system status
    tools        — List available tools
    memory       — Show recent memory
    joke         — Get a programming joke
    help         — Show this help

  Prefix messages with /tool <name> to run a tool directly.
  Example:  /tool calculate expression=2**32
            /tool web_search query=latest AI news
            /tool datetime
                """)
                continue

            # Direct tool call: /tool name key=val key=val
            if cmd.startswith("/tool "):
                parts = user_input[6:].strip().split()
                if not parts:
                    print("  Usage: /tool <name> [key=value ...]")
                    continue
                tool_name = parts[0]
                kwargs = {}
                for part in parts[1:]:
                    if "=" in part:
                        k, _, v = part.partition("=")
                        kwargs[k] = v
                    else:
                        kwargs["input"] = part
                import asyncio
                loop = asyncio.new_event_loop()
                result = loop.run_until_complete(self._core.run_tool(tool_name, **kwargs))
                loop.close()
                print(f"  [Tool: {tool_name}]\n  {result}\n")
                continue

            # Normal chat
            resp = self._core.chat_sync(
                user_input,
                force_provider=self._force_provider
            )

            provider_info = ""
            if resp.provider and resp.provider != "none":
                provider_info = f"  [{resp.provider}/{resp.model} · {resp.duration_ms:.0f}ms · {resp.tokens} tokens]"

            print(f"\nMAX: {resp.text}")
            if provider_info:
                print(provider_info)
            print()

            if resp.error:
                print(f"  [Error: {resp.error}]")

        if self._core:
            self._core.shutdown()
