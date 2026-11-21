"""
MAX AI — Workflow Automation Engine
LEREON Technologies

Allows users to create trigger → condition → action workflows.
All sensitive actions require confirmation. No arbitrary shell execution.
"""

import logging
import json
import time
import threading
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Callable, List
from pathlib import Path

logger = logging.getLogger("MAX.automation")
ROOT = Path(__file__).parent.parent


class TriggerType(Enum):
    MANUAL    = "manual"
    SCHEDULE  = "schedule"      # cron-like (HH:MM daily)
    KEYWORD   = "keyword"       # chat keyword triggers
    STARTUP   = "startup"
    SYSTEM    = "system"        # e.g. CPU > threshold


class ActionType(Enum):
    CHAT_MESSAGE   = "chat_message"    # Send a message to MAX
    OPEN_APP       = "open_app"        # Launch an application
    NOTIFY         = "notify"          # Desktop notification
    WEB_SEARCH     = "web_search"      # Search the web
    CLIPBOARD_COPY = "clipboard_copy"  # Copy text to clipboard
    SYSTEM_INFO    = "system_info"     # Get system info
    SPEAK          = "speak"           # Text-to-speech
    WAIT           = "wait"            # Delay (seconds)


SAFE_ACTIONS = {a.value for a in ActionType}  # Only these are allowed


@dataclass
class WorkflowStep:
    action: ActionType
    params: dict = field(default_factory=dict)
    delay_seconds: float = 0.0
    requires_confirmation: bool = False


@dataclass
class Workflow:
    id: str
    name: str
    description: str
    trigger: TriggerType
    trigger_params: dict
    steps: List[WorkflowStep]
    enabled: bool = True
    created_at: float = field(default_factory=time.time)
    last_run: Optional[float] = None
    run_count: int = 0
    tags: List[str] = field(default_factory=list)


class WorkflowEngine:
    """
    Manages workflow CRUD, scheduling, and execution.
    Uses safe allowlisted actions only. Never executes arbitrary shell commands.
    """

    def __init__(self, confirm_callback: Optional[Callable[[str], bool]] = None):
        self._workflows: dict[str, Workflow] = {}
        self._confirm_cb = confirm_callback or (lambda msg: False)
        self._scheduler_thread: Optional[threading.Thread] = None
        self._running = False
        self._action_callbacks: dict[str, Callable] = {}
        self._load()
        logger.info(f"Workflow engine ready. {len(self._workflows)} workflows loaded.")

    # ── Storage ───────────────────────────────────────────────────────────

    def _wf_path(self) -> Path:
        p = ROOT / "tasks" / "workflows.json"
        p.parent.mkdir(exist_ok=True)
        return p

    def _load(self):
        p = self._wf_path()
        if not p.exists():
            return
        try:
            data = json.loads(p.read_text())
            for item in data:
                wf = self._deserialize(item)
                if wf:
                    self._workflows[wf.id] = wf
        except Exception as e:
            logger.warning(f"Workflow load error: {e}")

    def _save(self):
        try:
            data = [self._serialize(wf) for wf in self._workflows.values()]
            self._wf_path().write_text(json.dumps(data, indent=2))
        except Exception as e:
            logger.error(f"Workflow save error: {e}")

    def _serialize(self, wf: Workflow) -> dict:
        return {
            "id": wf.id, "name": wf.name, "description": wf.description,
            "trigger": wf.trigger.value, "trigger_params": wf.trigger_params,
            "steps": [
                {"action": s.action.value, "params": s.params,
                 "delay": s.delay_seconds, "confirm": s.requires_confirmation}
                for s in wf.steps
            ],
            "enabled": wf.enabled,
            "created_at": wf.created_at,
            "last_run": wf.last_run,
            "run_count": wf.run_count,
            "tags": wf.tags,
        }

    def _deserialize(self, d: dict) -> Optional[Workflow]:
        try:
            steps = [
                WorkflowStep(
                    action=ActionType(s["action"]),
                    params=s.get("params", {}),
                    delay_seconds=s.get("delay", 0),
                    requires_confirmation=s.get("confirm", False),
                )
                for s in d.get("steps", [])
            ]
            return Workflow(
                id=d["id"], name=d["name"], description=d.get("description", ""),
                trigger=TriggerType(d["trigger"]),
                trigger_params=d.get("trigger_params", {}),
                steps=steps,
                enabled=d.get("enabled", True),
                created_at=d.get("created_at", time.time()),
                last_run=d.get("last_run"),
                run_count=d.get("run_count", 0),
                tags=d.get("tags", []),
            )
        except Exception as e:
            logger.warning(f"Deserialize workflow failed: {e}")
            return None

    # ── CRUD ──────────────────────────────────────────────────────────────

    def create(self, name: str, description: str, trigger: TriggerType,
               trigger_params: dict, steps: List[WorkflowStep]) -> Workflow:
        wf = Workflow(
            id=str(uuid.uuid4())[:8],
            name=name, description=description,
            trigger=trigger, trigger_params=trigger_params,
            steps=steps
        )
        self._workflows[wf.id] = wf
        self._save()
        logger.info(f"Workflow created: '{name}' [{wf.id}]")
        return wf

    def update(self, wf_id: str, **kwargs) -> bool:
        wf = self._workflows.get(wf_id)
        if not wf:
            return False
        for k, v in kwargs.items():
            if hasattr(wf, k):
                setattr(wf, k, v)
        self._save()
        return True

    def delete(self, wf_id: str) -> bool:
        if wf_id in self._workflows:
            del self._workflows[wf_id]
            self._save()
            return True
        return False

    def get(self, wf_id: str) -> Optional[Workflow]:
        return self._workflows.get(wf_id)

    def list_all(self) -> list:
        return sorted(self._workflows.values(), key=lambda w: w.created_at, reverse=True)

    def enable(self, wf_id: str, enabled: bool):
        wf = self._workflows.get(wf_id)
        if wf:
            wf.enabled = enabled
            self._save()

    # ── Execution ─────────────────────────────────────────────────────────

    def register_action_handler(self, action: ActionType, handler: Callable):
        """Register external handler for an action type (e.g. UI notification)."""
        self._action_callbacks[action.value] = handler

    def run_workflow(self, wf_id: str) -> dict:
        """Execute a workflow. Returns {"ok": bool, "results": list, "error": str}"""
        wf = self._workflows.get(wf_id)
        if not wf:
            return {"ok": False, "results": [], "error": f"Workflow '{wf_id}' not found."}
        if not wf.enabled:
            return {"ok": False, "results": [], "error": "Workflow is disabled."}

        logger.info(f"Running workflow: '{wf.name}' [{wf.id}]")
        results = []

        for i, step in enumerate(wf.steps):
            if step.action.value not in SAFE_ACTIONS:
                results.append({"step": i, "ok": False, "result": f"Blocked unsafe action: {step.action.value}"})
                continue

            if step.delay_seconds > 0:
                time.sleep(min(step.delay_seconds, 30))  # Cap delay at 30s

            if step.requires_confirmation:
                ok = self._confirm_cb(
                    f"Workflow '{wf.name}' — Step {i+1}: {step.action.value}({step.params})"
                )
                if not ok:
                    results.append({"step": i, "ok": False, "result": "User denied confirmation."})
                    continue

            result = self._execute_step(step)
            results.append({"step": i, "action": step.action.value, "ok": True, "result": result})

        wf.last_run = time.time()
        wf.run_count += 1
        self._save()
        return {"ok": True, "results": results, "error": ""}

    def _execute_step(self, step: WorkflowStep) -> str:
        handler = self._action_callbacks.get(step.action.value)
        if handler:
            try:
                return str(handler(**step.params))
            except Exception as e:
                return f"Handler error: {e}"

        # Built-in fallbacks
        if step.action == ActionType.WAIT:
            secs = min(float(step.params.get("seconds", 1)), 30)
            time.sleep(secs)
            return f"Waited {secs}s"

        if step.action == ActionType.CLIPBOARD_COPY:
            text = step.params.get("text", "")
            try:
                import pyperclip
                pyperclip.copy(text)
                return f"Copied to clipboard: {text[:50]}"
            except Exception as e:
                return f"Clipboard error: {e}"

        if step.action == ActionType.SYSTEM_INFO:
            try:
                import psutil
                return (f"CPU: {psutil.cpu_percent()}%  "
                        f"RAM: {psutil.virtual_memory().percent}%")
            except Exception as e:
                return f"System info error: {e}"

        return f"No handler registered for {step.action.value}"

    # ── Scheduler ─────────────────────────────────────────────────────────

    def start_scheduler(self):
        """Start background scheduler for time-based workflows."""
        if self._running:
            return
        self._running = True
        self._scheduler_thread = threading.Thread(
            target=self._scheduler_loop, daemon=True, name="MAX-Scheduler"
        )
        self._scheduler_thread.start()
        logger.info("Workflow scheduler started.")

    def stop_scheduler(self):
        self._running = False

    def _scheduler_loop(self):
        while self._running:
            now_struct = time.localtime()
            current_hhmm = f"{now_struct.tm_hour:02d}:{now_struct.tm_min:02d}"
            for wf in list(self._workflows.values()):
                if not wf.enabled:
                    continue
                if wf.trigger == TriggerType.SCHEDULE:
                    scheduled = wf.trigger_params.get("time", "")
                    if scheduled == current_hhmm:
                        # Avoid re-running within the same minute
                        if wf.last_run and (time.time() - wf.last_run) < 55:
                            continue
                        logger.info(f"Scheduled trigger: '{wf.name}'")
                        threading.Thread(
                            target=self.run_workflow, args=(wf.id,), daemon=True
                        ).start()
                elif wf.trigger == TriggerType.STARTUP:
                    if wf.run_count == 0:
                        logger.info(f"Startup trigger: '{wf.name}'")
                        threading.Thread(
                            target=self.run_workflow, args=(wf.id,), daemon=True
                        ).start()
            time.sleep(60)

    def check_keyword_trigger(self, text: str) -> list:
        """Check if any keyword workflows should fire. Returns list of wf ids."""
        text_lower = text.lower()
        triggered = []
        for wf in self._workflows.values():
            if not wf.enabled or wf.trigger != TriggerType.KEYWORD:
                continue
            keyword = wf.trigger_params.get("keyword", "").lower()
            if keyword and keyword in text_lower:
                triggered.append(wf.id)
        return triggered
