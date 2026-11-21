"""
MAX AI — Core Engine v2 (UPGRADED)
LEREON Technologies

Central coordinator: chat, providers, tools, memory, tasks,
personality, knowledge base, plugins, automation, monitor.
"""

import logging
import asyncio
import time
import uuid
from typing import Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("MAX.core")


class MAXState(Enum):
    IDLE             = "idle"
    LISTENING        = "listening"
    THINKING         = "thinking"
    EXECUTING        = "executing"
    SPEAKING         = "speaking"
    BROWSING         = "browsing"
    ANALYZING        = "analyzing"
    ERROR            = "error"
    OFFLINE          = "offline"
    WAITING_APPROVAL = "waiting_approval"


@dataclass
class ChatMessage:
    role: str
    content: str
    timestamp: float = field(default_factory=time.time)
    provider: str = ""
    tokens: int = 0


@dataclass
class ChatResponse:
    text: str
    provider: str
    model: str
    state: MAXState = MAXState.IDLE
    error: Optional[str] = None
    duration_ms: float = 0.0
    tokens: int = 0


class MAXCore:
    def __init__(self):
        from core.config import get_config
        self.config = get_config()
        self.session_id = str(uuid.uuid4())[:8]
        self.state = MAXState.IDLE
        self.conversation: list = []
        self._state_cbs: list = []

        # Subsystem singletons (lazy)
        self._router        = None
        self._memory        = None
        self._tools         = None
        self._tasks         = None
        self._voice         = None
        self._personality   = None
        self._knowledge     = None
        self._plugins       = None
        self._automation    = None
        self._monitor       = None
        self._productivity  = None
        self._studio        = None
        self._vision        = None
        self._desktop       = None

        logger.info(f"MAX Core v2 online — session {self.session_id}")

    # ── Subsystems ────────────────────────────────────────────────────────

    @property
    def router(self):
        if self._router is None:
            from providers.router import ProviderRouter
            self._router = ProviderRouter()
        return self._router

    @property
    def memory(self):
        if self._memory is None:
            from memory.memory_engine import MemoryEngine
            self._memory = MemoryEngine()
        return self._memory

    @property
    def tools(self):
        if self._tools is None:
            from tools.all_tools import ToolRegistry
            self._tools = ToolRegistry()
        return self._tools

    @property
    def tasks(self):
        if self._tasks is None:
            from tasks.task_manager import TaskManager
            self._tasks = TaskManager()
        return self._tasks

    @property
    def voice(self):
        if self._voice is None:
            from voice.voice_engine import VoiceEngine
            self._voice = VoiceEngine(self.config)
        return self._voice

    @property
    def personality(self):
        if self._personality is None:
            from personality.personality_engine import PersonalityEngine
            self._personality = PersonalityEngine(self.config)
        return self._personality

    @property
    def knowledge(self):
        if self._knowledge is None:
            from knowledge.knowledge_base import KnowledgeBase
            self._knowledge = KnowledgeBase()
        return self._knowledge

    @property
    def plugins(self):
        if self._plugins is None:
            from plugins.plugin_manager import PluginManager
            self._plugins = PluginManager(core=self)
        return self._plugins

    @property
    def automation(self):
        if self._automation is None:
            from automation.workflow_engine import WorkflowEngine
            self._automation = WorkflowEngine()
        return self._automation

    @property
    def monitor(self):
        if self._monitor is None:
            from monitor.system_monitor import SystemMonitor
            self._monitor = SystemMonitor()
            self._monitor.start()
        return self._monitor

    @property
    def productivity(self):
        if self._productivity is None:
            from productivity.productivity_engine import ProductivityEngine
            self._productivity = ProductivityEngine()
        return self._productivity

    @property
    def studio(self):
        if self._studio is None:
            from studio.studio_engine import StudioEngine
            self._studio = StudioEngine(core=self)
        return self._studio

    @property
    def vision(self):
        if self._vision is None:
            from vision.vision_engine import VisionEngine
            self._vision = VisionEngine(config=self.config)
        return self._vision

    @property
    def desktop(self):
        if self._desktop is None:
            from core.desktop_control import DesktopControl
            self._desktop = DesktopControl(config=self.config)
        return self._desktop

    # ── State ─────────────────────────────────────────────────────────────

    def set_state(self, s: MAXState):
        if self.state != s:
            self.state = s
            for cb in self._state_cbs:
                try:
                    cb(s)
                except Exception:
                    pass

    def on_state_change(self, cb: Callable):
        self._state_cbs.append(cb)

    # ── Main chat ─────────────────────────────────────────────────────────

    async def chat(
        self,
        user_input: str,
        force_provider: Optional[str] = None,
        image_bytes: Optional[bytes] = None,
    ) -> ChatResponse:
        start = time.time()
        self.set_state(MAXState.THINKING)

        self.conversation.append(ChatMessage(role="user", content=user_input))

        # Memory context
        ctx = ""
        if self.config.memory_enabled:
            try:
                ctx = self.memory.get_context(user_input)
            except Exception as e:
                logger.warning(f"Memory read: {e}")

        # Knowledge base context
        kb_ctx = ""
        try:
            kb_ctx = self.knowledge.get_context_for_query(user_input)
        except Exception:
            pass

        # Automation keyword triggers (fire and forget)
        try:
            triggered = self.automation.check_keyword_trigger(user_input)
            for wf_id in triggered:
                import threading
                threading.Thread(
                    target=self.automation.run_workflow, args=(wf_id,), daemon=True
                ).start()
        except Exception:
            pass

        # Build messages
        msgs = self._build_messages(ctx, kb_ctx)

        # Build personality-enhanced system prompt
        system_prompt = self.personality.build_system_prompt()

        # Add tools description
        try:
            tool_names = self.tools.names()
            if tool_names:
                system_prompt += f"\n\nAvailable tools: {', '.join(tool_names)}"
        except Exception:
            pass

        # Select provider
        pname = force_provider or self.config.default_provider
        provider = None
        if pname:
            try:
                provider = self.router.get(pname)
            except Exception as e:
                logger.warning(f"Provider '{pname}': {e}")

        if provider is None:
            provider = self.router.get_fallback(exclude=[pname] if pname else [])

        if provider is None:
            self.set_state(MAXState.OFFLINE)
            return ChatResponse(
                text=(
                    "⚠️ **No AI providers available.**\n\n"
                    "Add an API key via **Settings → API Keys**, or edit your `.env` file.\n\n"
                    "Supported: OpenAI · Anthropic · Gemini · Groq · DeepSeek · Mistral · OpenRouter · Ollama"
                ),
                provider="none", model="none",
                state=MAXState.OFFLINE,
                error="No providers configured"
            )

        # Generate
        try:
            resp_text, model, tokens = await provider.complete(
                messages=msgs, system=system_prompt,
            )
        except Exception as e:
            logger.error(f"Provider {provider.name}: {e}")
            self.set_state(MAXState.ERROR)
            return ChatResponse(
                text=f"❌ Provider error ({provider.name}): {e}",
                provider=provider.name, model="",
                state=MAXState.ERROR, error=str(e)
            )

        # Plugin post-processing
        try:
            resp_text = self.plugins.notify_chat(user_input, resp_text)
        except Exception:
            pass

        # Store
        self.conversation.append(ChatMessage(
            role="assistant", content=resp_text,
            provider=provider.name, tokens=tokens
        ))

        if self.config.memory_enabled:
            try:
                self.memory.store(user_input, resp_text)
            except Exception as e:
                logger.warning(f"Memory write: {e}")

        ms = (time.time() - start) * 1000
        self.set_state(MAXState.IDLE)
        return ChatResponse(
            text=resp_text, provider=provider.name, model=model,
            state=MAXState.IDLE, duration_ms=ms, tokens=tokens
        )

    def chat_sync(self, user_input: str, **kwargs) -> ChatResponse:
        """Thread-safe synchronous wrapper."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self.chat(user_input, **kwargs))
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"chat_sync: {e}")
            return ChatResponse(
                text=f"Error: {e}", provider="none", model="",
                state=MAXState.ERROR, error=str(e)
            )

    def _build_messages(self, ctx: str = "", kb_ctx: str = "") -> list:
        msgs = []
        if ctx:
            msgs.append({"role": "system", "content": f"[Conversation memory]\n{ctx}"})
        if kb_ctx:
            msgs.append({"role": "system", "content": kb_ctx})
        max_h = self.config.get("memory", "max_history", default=50)
        for m in self.conversation[-(max_h * 2):]:
            if m.role in ("user", "assistant"):
                msgs.append({"role": m.role, "content": m.content})
        return msgs

    # ── Multi-model collaboration ─────────────────────────────────────────

    async def collaborate(self, task: str, provider_names: list) -> dict:
        """
        Multi-model collaboration:
        Provider 1 → researches
        Provider 2 → analyzes
        Provider 3 → reviews
        Final provider → synthesizes
        """
        results = {}
        roles = ["Research", "Analysis", "Review", "Synthesis"]
        previous = ""

        for i, pname in enumerate(provider_names):
            role = roles[i] if i < len(roles) else f"Step {i+1}"
            try:
                provider = self.router.get(pname)
            except Exception as e:
                results[role] = f"Provider '{pname}' unavailable: {e}"
                continue

            if i == 0:
                prompt = f"Research the following topic thoroughly:\n\n{task}"
            elif i == len(provider_names) - 1:
                prompt = (
                    f"Synthesize all previous findings into a final, comprehensive answer.\n\n"
                    f"Original task: {task}\n\nPrevious work:\n{previous}"
                )
            else:
                prompt = (
                    f"You are performing the '{role}' step.\n"
                    f"Original task: {task}\n\nPrevious work:\n{previous}\n\n"
                    f"Contribute your analysis."
                )

            try:
                text, model, _ = await provider.complete(
                    messages=[{"role": "user", "content": prompt}],
                    system=self.personality.build_system_prompt()
                )
                results[f"{role} ({pname}/{model})"] = text
                previous += f"\n\n[{role}]\n{text}"
            except Exception as e:
                results[role] = f"Error: {e}"

        return results

    # ── Tool execution ────────────────────────────────────────────────────

    async def run_tool(self, tool_name: str, **kwargs) -> str:
        self.set_state(MAXState.EXECUTING)
        try:
            tool = self.tools.get(tool_name)
            if tool is None:
                return f"Tool '{tool_name}' not found."
            if not tool.allowed(self.config):
                return f"Permission denied for '{tool_name}'."
            return await tool.run(**kwargs)
        except Exception as e:
            return f"Tool error: {e}"
        finally:
            self.set_state(MAXState.IDLE)

    # ── Conversation management ───────────────────────────────────────────

    def clear_conversation(self):
        self.conversation.clear()

    def get_history(self) -> list:
        return list(self.conversation)

    # ── Status ────────────────────────────────────────────────────────────

    def status(self) -> dict:
        return {
            "state": self.state.value,
            "session": self.session_id,
            "default_provider": self.config.default_provider,
            "enabled_providers": self.config.enabled_providers,
            "conversation_turns": len(self.conversation),
            "memory_enabled": self.config.memory_enabled,
            "personality_mode": self.personality.settings.mode.value,
        }

    def shutdown(self):
        logger.info("MAX Core shutting down...")
        for attr, method in [
            ("_memory", "close"), ("_productivity", "close"),
            ("_knowledge", "close"), ("_voice", "shutdown"),
            ("_tasks", "shutdown"), ("_monitor", "stop"),
            ("_automation", "stop_scheduler"),
            ("_vision", "stop_gesture_control"),
        ]:
            obj = getattr(self, attr, None)
            if obj and hasattr(obj, method):
                try:
                    getattr(obj, method)()
                except Exception:
                    pass
        logger.info("MAX Core stopped.")
