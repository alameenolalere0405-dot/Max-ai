"""MAX AI — Memory Tool — LEREON Technologies"""


class MemoryTool:
    """Stub memory tool — real memory handled by MemoryEngine."""
    name = "memory_recall"
    description = "Recall saved facts and preferences from memory"
    permission_key = "memory"

    def allowed(self, config) -> bool:
        return config.permission("memory") if config else True

    async def run(self, query: str = "", **kwargs) -> str:
        return f"Memory query: '{query}' — use the Memory tab to view full history."
