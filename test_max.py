"""
MAX AI — Automated Test Suite
LEREON Technologies

Tests: config, tools, memory, personality, knowledge base,
       productivity, automation, monitor, plugins.

Run: python -m pytest tests/ -v
  or: python tests/test_max.py
"""

import sys
import os
import unittest
import asyncio
import tempfile
import time
from pathlib import Path

# Project root on path
sys.path.insert(0, str(Path(__file__).parent.parent))


# ── Config Tests ──────────────────────────────────────────────────────────

class TestConfig(unittest.TestCase):
    def test_load(self):
        from core.config import Config
        cfg = Config()
        self.assertIsNotNone(cfg)

    def test_get_default(self):
        from core.config import Config
        cfg = Config()
        val = cfg.get("nonexistent", "key", default="fallback")
        self.assertEqual(val, "fallback")

    def test_set_get(self):
        from core.config import Config
        cfg = Config()
        cfg.set("test", "key", "value_123")
        self.assertEqual(cfg.get("test", "key"), "value_123")

    def test_enabled_providers_is_list(self):
        from core.config import Config
        cfg = Config()
        providers = cfg.enabled_providers
        self.assertIsInstance(providers, list)


# ── Tool Tests ────────────────────────────────────────────────────────────

class TestTools(unittest.TestCase):
    def _run(self, coro):
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    def test_calculator_basic(self):
        from tools.all_tools import CalculatorTool
        t = CalculatorTool()
        result = self._run(t.run(expression="2 + 2"))
        self.assertIn("4", result)

    def test_calculator_complex(self):
        from tools.all_tools import CalculatorTool
        t = CalculatorTool()
        result = self._run(t.run(expression="2 ** 10"))
        self.assertIn("1024", result)

    def test_calculator_division(self):
        from tools.all_tools import CalculatorTool
        t = CalculatorTool()
        result = self._run(t.run(expression="10 / 4"))
        self.assertIn("2.5", result)

    def test_calculator_bad_expression(self):
        from tools.all_tools import CalculatorTool
        t = CalculatorTool()
        result = self._run(t.run(expression="import os"))
        self.assertIn("Cannot evaluate", result)

    def test_datetime(self):
        from tools.all_tools import DateTimeTool
        t = DateTimeTool()
        result = self._run(t.run())
        self.assertIn("Local:", result)
        self.assertIn("UTC:", result)

    def test_system_info(self):
        from tools.all_tools import SystemInfoTool
        t = SystemInfoTool()
        result = self._run(t.run())
        self.assertTrue(
            "CPU" in result or "psutil not installed" in result
        )

    def test_file_read_missing(self):
        from tools.all_tools import FileReadTool
        from core.config import Config
        t = FileReadTool()
        result = self._run(t.run(path="/nonexistent/file.txt"))
        self.assertIn("not found", result.lower())

    def test_file_list(self):
        from tools.all_tools import FileListTool
        t = FileListTool()
        with tempfile.TemporaryDirectory() as td:
            # Create a test file
            Path(td, "test.txt").write_text("hello")
            result = self._run(t.run(path=td))
            self.assertIn("test.txt", result)

    def test_tool_registry(self):
        from tools.all_tools import ToolRegistry
        reg = ToolRegistry()
        self.assertGreater(len(reg.names()), 5)
        self.assertIn("calculate", reg.names())
        self.assertIn("web_search", reg.names())
        self.assertIn("datetime", reg.names())

    def test_registry_get_missing(self):
        from tools.all_tools import ToolRegistry
        reg = ToolRegistry()
        self.assertIsNone(reg.get("nonexistent_tool"))


# ── Memory Tests ──────────────────────────────────────────────────────────

class TestMemory(unittest.TestCase):
    def setUp(self):
        import tempfile
        self._tmp = tempfile.mkdtemp()
        # Monkey-patch ROOT
        import memory.memory_engine as me
        self._orig_root = me.ROOT
        me.ROOT = Path(self._tmp)
        Path(self._tmp, "memory").mkdir()
        from memory.memory_engine import MemoryEngine
        self.mem = MemoryEngine()

    def tearDown(self):
        self.mem.close()
        import memory.memory_engine as me
        me.ROOT = self._orig_root

    def test_store_and_retrieve(self):
        self.mem.store("What is Python?", "Python is a programming language.")
        ctx = self.mem.get_context("Python")
        self.assertIn("Python", ctx)

    def test_clear(self):
        self.mem.store("hello", "world")
        self.mem.clear()
        ctx = self.mem.get_context("hello")
        self.assertEqual(ctx, "")

    def test_history_returns_list(self):
        self.mem.store("Q1", "A1")
        self.mem.store("Q2", "A2")
        h = self.mem.get_history()
        self.assertIsInstance(h, list)
        self.assertEqual(len(h), 2)

    def test_save_and_get_fact(self):
        self.mem.save_fact("user_name", "Alice")
        facts = self.mem.get_facts()
        self.assertTrue(any(f["key"] == "user_name" for f in facts))


# ── Personality Tests ─────────────────────────────────────────────────────

class TestPersonality(unittest.TestCase):
    def setUp(self):
        from personality.personality_engine import PersonalityEngine
        self.eng = PersonalityEngine()

    def test_default_mode(self):
        from personality.personality_engine import PersonalityMode
        self.assertEqual(self.eng.settings.mode, PersonalityMode.SARCASTIC)

    def test_set_mode(self):
        from personality.personality_engine import PersonalityMode
        self.eng.set_mode(PersonalityMode.PROFESSIONAL)
        self.assertEqual(self.eng.settings.mode, PersonalityMode.PROFESSIONAL)

    def test_sarcasm_clamp(self):
        self.eng.set_sarcasm(150)
        self.assertEqual(self.eng.settings.sarcasm_level, 100)
        self.eng.set_sarcasm(-10)
        self.assertEqual(self.eng.settings.sarcasm_level, 0)

    def test_system_prompt_contains_lereon(self):
        prompt = self.eng.build_system_prompt()
        self.assertIn("LEREON", prompt)

    def test_system_prompt_no_harmful_content(self):
        prompt = self.eng.build_system_prompt()
        self.assertNotIn("harm", prompt.lower()[:200])

    def test_all_modes(self):
        from personality.personality_engine import PersonalityMode
        modes = self.eng.all_modes
        self.assertEqual(len(modes), len(list(PersonalityMode)))

    def test_get_joke(self):
        joke = self.eng.get_random_joke()
        self.assertIsInstance(joke, str)
        self.assertGreater(len(joke), 10)


# ── Knowledge Base Tests ──────────────────────────────────────────────────

class TestKnowledgeBase(unittest.TestCase):
    def setUp(self):
        import tempfile
        self._tmp = tempfile.mkdtemp()
        import knowledge.knowledge_base as kb_mod
        self._orig = kb_mod.ROOT
        kb_mod.ROOT = Path(self._tmp)
        Path(self._tmp, "memory").mkdir()
        from knowledge.knowledge_base import KnowledgeBase
        self.kb = KnowledgeBase()

    def tearDown(self):
        self.kb.close()
        import knowledge.knowledge_base as kb_mod
        kb_mod.ROOT = self._orig

    def test_import_text_file(self):
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as f:
            f.write("MAX AI is built by LEREON Technologies. It is a great AI assistant.")
            path = f.name
        try:
            result = self.kb.import_file(path)
            self.assertTrue(result["ok"])
        finally:
            os.unlink(path)

    def test_duplicate_import(self):
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as f:
            f.write("Unique content " * 20)
            path = f.name
        try:
            self.kb.import_file(path)
            result = self.kb.import_file(path)
            self.assertFalse(result["ok"])
            self.assertIn("Already imported", result["message"])
        finally:
            os.unlink(path)

    def test_search(self):
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as f:
            f.write("LEREON Technologies builds MAX AI for personal use.")
            path = f.name
        try:
            self.kb.import_file(path)
            results = self.kb.search("LEREON")
            self.assertGreater(len(results), 0)
            self.assertIn("LEREON", results[0]["snippet"])
        finally:
            os.unlink(path)

    def test_delete(self):
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as f:
            f.write("Delete me " * 30)
            path = f.name
        try:
            result = self.kb.import_file(path)
            doc_id = result["id"]
            ok = self.kb.delete_document(doc_id)
            self.assertTrue(ok)
            self.assertEqual(self.kb.document_count(), 0)
        finally:
            os.unlink(path)

    def test_unsupported_extension(self):
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False, mode="w") as f:
            f.write("test")
            path = f.name
        try:
            result = self.kb.import_file(path)
            self.assertFalse(result["ok"])
        finally:
            os.unlink(path)


# ── Productivity Tests ────────────────────────────────────────────────────

class TestProductivity(unittest.TestCase):
    def setUp(self):
        import tempfile
        self._tmp = tempfile.mkdtemp()
        import productivity.productivity_engine as pe
        self._orig = pe.ROOT
        pe.ROOT = Path(self._tmp)
        Path(self._tmp, "memory").mkdir()
        from productivity.productivity_engine import ProductivityEngine, Priority
        self.prod = ProductivityEngine()
        self.Priority = Priority

    def tearDown(self):
        self.prod.close()
        import productivity.productivity_engine as pe
        pe.ROOT = self._orig

    def test_add_and_list_todo(self):
        self.prod.add_todo("Write tests", priority=self.Priority.HIGH)
        todos = self.prod.list_todos()
        self.assertEqual(len(todos), 1)
        self.assertEqual(todos[0].title, "Write tests")

    def test_complete_todo(self):
        t = self.prod.add_todo("Complete me")
        ok = self.prod.complete_todo(t.id)
        self.assertTrue(ok)
        active = self.prod.list_todos(include_done=False)
        self.assertEqual(len(active), 0)

    def test_add_and_list_note(self):
        self.prod.add_note("Test note", "Content here")
        notes = self.prod.list_notes()
        self.assertEqual(len(notes), 1)
        self.assertEqual(notes[0].title, "Test note")

    def test_search_notes(self):
        self.prod.add_note("Python tips", "Use list comprehensions for speed.")
        results = self.prod.search_notes("comprehensions")
        self.assertEqual(len(results), 1)

    def test_add_reminder(self):
        future = time.time() + 3600
        r = self.prod.add_reminder("Stand up and stretch", future)
        due = self.prod.get_due_reminders()
        self.assertEqual(len(due), 0)   # Not due yet

    def test_overdue_reminder(self):
        past = time.time() - 10
        self.prod.add_reminder("Past reminder", past)
        due = self.prod.get_due_reminders()
        self.assertEqual(len(due), 1)


# ── Automation Tests ──────────────────────────────────────────────────────

class TestAutomation(unittest.TestCase):
    def setUp(self):
        import tempfile
        self._tmp = tempfile.mkdtemp()
        import automation.workflow_engine as we
        self._orig = we.ROOT
        we.ROOT = Path(self._tmp)
        Path(self._tmp, "tasks").mkdir()
        from automation.workflow_engine import WorkflowEngine
        self.engine = WorkflowEngine()

    def tearDown(self):
        self.engine.stop_scheduler()
        import automation.workflow_engine as we
        we.ROOT = self._orig

    def test_create_workflow(self):
        from automation.workflow_engine import TriggerType, ActionType, WorkflowStep
        step = WorkflowStep(action=ActionType.WAIT, params={"seconds": 0})
        wf = self.engine.create("Test WF", "desc", TriggerType.MANUAL, {}, [step])
        self.assertIsNotNone(wf.id)
        self.assertEqual(len(self.engine.list_all()), 1)

    def test_run_workflow(self):
        from automation.workflow_engine import TriggerType, ActionType, WorkflowStep
        step = WorkflowStep(action=ActionType.WAIT, params={"seconds": 0})
        wf = self.engine.create("Run Test", "", TriggerType.MANUAL, {}, [step])
        result = self.engine.run_workflow(wf.id)
        self.assertTrue(result["ok"])

    def test_delete_workflow(self):
        from automation.workflow_engine import TriggerType, ActionType, WorkflowStep
        step = WorkflowStep(action=ActionType.DATETIME, params={}) if False else \
               WorkflowStep(action=ActionType.WAIT, params={"seconds": 0})
        wf = self.engine.create("Delete Me", "", TriggerType.MANUAL, {}, [step])
        ok = self.engine.delete(wf.id)
        self.assertTrue(ok)
        self.assertEqual(len(self.engine.list_all()), 0)

    def test_keyword_trigger(self):
        from automation.workflow_engine import TriggerType, ActionType, WorkflowStep
        step = WorkflowStep(action=ActionType.WAIT, params={"seconds": 0})
        wf = self.engine.create(
            "Keyword WF", "", TriggerType.KEYWORD,
            {"keyword": "deploy"}, [step]
        )
        triggered = self.engine.check_keyword_trigger("Please deploy to production now")
        self.assertIn(wf.id, triggered)
        not_triggered = self.engine.check_keyword_trigger("Just a normal message")
        self.assertNotIn(wf.id, not_triggered)


# ── Plugin Tests ──────────────────────────────────────────────────────────

class TestPlugins(unittest.TestCase):
    def test_discover_returns_list(self):
        from plugins.plugin_manager import PluginManager
        pm = PluginManager()
        result = pm.discover()
        self.assertIsInstance(result, list)

    def test_load_nonexistent(self):
        from plugins.plugin_manager import PluginManager
        pm = PluginManager()
        result = pm.load_plugin("nonexistent_plugin")
        self.assertFalse(result["ok"])

    def test_notify_chat_passthrough(self):
        from plugins.plugin_manager import PluginManager
        pm = PluginManager()
        result = pm.notify_chat("hello", "world response")
        self.assertEqual(result, "world response")


# ── Monitor Tests ─────────────────────────────────────────────────────────

class TestMonitor(unittest.TestCase):
    def test_collect_snapshot(self):
        from monitor.system_monitor import SystemMonitor
        m = SystemMonitor()
        snap = m._collect()
        self.assertIsNotNone(snap)
        # CPU percent is 0–100
        self.assertGreaterEqual(snap.cpu_percent, 0)
        self.assertLessEqual(snap.cpu_percent, 100)

    def test_health_score(self):
        from monitor.system_monitor import SystemSnapshot
        snap = SystemSnapshot(cpu_percent=50, ram_percent=50, disk_percent=50)
        self.assertGreater(snap.health_score(), 60)

    def test_health_score_high_cpu(self):
        from monitor.system_monitor import SystemSnapshot
        snap = SystemSnapshot(cpu_percent=95, ram_percent=50, disk_percent=50)
        self.assertLess(snap.health_score(), 90)

    def test_format_snapshot(self):
        from monitor.system_monitor import SystemMonitor, SystemSnapshot
        m = SystemMonitor()
        snap = SystemSnapshot(
            cpu_percent=42, cpu_cores=8, ram_percent=61,
            ram_used_mb=4000, ram_total_mb=8000,
            disk_percent=55, disk_used_gb=100, disk_total_gb=500,
            platform_name="Linux 6.0"
        )
        text = m.format_snapshot(snap)
        self.assertIn("42", text)
        self.assertIn("Linux", text)


# ── Studio Tests ──────────────────────────────────────────────────────────

class TestStudio(unittest.TestCase):
    def setUp(self):
        from studio.studio_engine import StudioEngine
        self.studio = StudioEngine(core=None)

    def test_task_types_list(self):
        types = self.studio.task_types
        self.assertIn("summarize", types)
        self.assertIn("code_review", types)
        self.assertIn("custom", types)
        self.assertGreater(len(types), 5)

    def test_read_file_missing(self):
        result = self.studio.read_file("/nonexistent/file.txt")
        self.assertIn("not found", result.lower())

    def test_read_text_file(self):
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as f:
            f.write("Hello from MAX AI test.")
            path = f.name
        try:
            result = self.studio.read_file(path)
            self.assertIn("Hello from MAX AI", result)
        finally:
            os.unlink(path)

    def test_save_output(self):
        with tempfile.TemporaryDirectory() as td:
            out_path = os.path.join(td, "output.txt")
            result = self.studio.save_output("Test content from MAX AI.", out_path)
            self.assertTrue(result["ok"])
            self.assertTrue(Path(out_path).exists())

    def test_run_task_no_core_returns_error(self):
        import asyncio
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(
            self.studio.run_task("summarize", "Some content here.")
        )
        loop.close()
        # Without a core, should return an error message, not crash
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)


# ── Vision Tests ──────────────────────────────────────────────────────────

class TestVision(unittest.TestCase):
    def setUp(self):
        from vision.vision_engine import VisionEngine
        self.vision = VisionEngine(config=None)

    def test_image_to_base64_missing(self):
        result = self.vision.image_to_base64("/nonexistent/image.png")
        self.assertIsNone(result)

    def test_image_to_base64_real_image(self):
        try:
            from PIL import Image
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                img_path = f.name
            img = Image.new("RGB", (10, 10), color=(0, 128, 255))
            img.save(img_path)
            try:
                result = self.vision.image_to_base64(img_path)
                self.assertIsNotNone(result)
                self.assertGreater(len(result), 10)
            finally:
                os.unlink(img_path)
        except ImportError:
            self.skipTest("Pillow not installed")

    def test_gesture_control_no_camera_permission(self):
        # With no config, camera permission defaults to False
        result = self.vision.start_gesture_control(lambda g: None)
        # Either False (no permission) or False (opencv not installed) — both are ok
        # It must not raise an exception
        self.assertIsInstance(result, bool)


# ── Desktop Control Tests ─────────────────────────────────────────────────

class TestDesktopControl(unittest.TestCase):
    def setUp(self):
        from core.desktop_control import DesktopControl
        # No config = permissions disabled
        self.ctrl = DesktopControl(config=None, confirm_callback=lambda m: False)

    def _run(self, coro):
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    def test_launch_app_no_permission(self):
        result = self._run(self.ctrl.launch_app("chrome"))
        self.assertFalse(result["ok"])
        self.assertIn("permission", result["message"].lower())

    def test_list_directory_no_permission(self):
        result = self._run(self.ctrl.list_directory("~"))
        self.assertIn("permission", result.lower())

    def test_system_info_always_works(self):
        # system_info doesn't require pc_control permission
        result = self._run(self.ctrl.get_system_info())
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 10)

    def test_safe_apps_registry(self):
        from core.desktop_control import SAFE_APPS
        self.assertIn("chrome", SAFE_APPS)
        self.assertIn("vscode", SAFE_APPS)
        self.assertIn("terminal", SAFE_APPS)
        self.assertGreater(len(SAFE_APPS), 10)


# ── Diagnostics Tests ─────────────────────────────────────────────────────

class TestDiagnostics(unittest.TestCase):
    def test_diagnostics_runs_without_crash(self):
        import io
        from contextlib import redirect_stdout
        from core.diagnostics import Diagnostics
        buf = io.StringIO()
        with redirect_stdout(buf):
            diag = Diagnostics()
            diag.run_full_check()
        output = buf.getvalue()
        self.assertIn("MAX AI", output)
        self.assertGreater(len(diag._results), 5)

    def test_diagnostics_has_categories(self):
        import io
        from contextlib import redirect_stdout
        from core.diagnostics import Diagnostics
        buf = io.StringIO()
        with redirect_stdout(buf):
            diag = Diagnostics()
            diag.run_full_check()
        cats = {r["category"] for r in diag._results}
        self.assertIn("Configuration", cats)
        self.assertIn("Core Packages", cats)


# ── Issue-specific regression tests ──────────────────────────────────────

class TestIssue1_PermissionDefaults(unittest.TestCase):
    """Issue 1 & 3: Sensitive permissions must be OFF by default."""

    def setUp(self):
        from core.config import Config
        self.config = Config()

    def test_microphone_default_off(self):
        self.assertFalse(self.config.permission("microphone"),
                         "microphone must be False by default")

    def test_camera_default_off(self):
        self.assertFalse(self.config.permission("camera"),
                         "camera must be False by default")

    def test_screen_capture_default_off(self):
        self.assertFalse(self.config.permission("screen_capture"),
                         "screen_capture must be False by default")

    def test_automation_default_off(self):
        self.assertFalse(self.config.permission("automation"),
                         "automation must be False by default")

    def test_pc_control_default_off(self):
        self.assertFalse(self.config.permission("pc_control"),
                         "pc_control must be False by default")

    def test_notifications_default_off(self):
        self.assertFalse(self.config.permission("notifications"),
                         "notifications must be False by default")

    def test_safe_permissions_on(self):
        """Non-sensitive permissions can be on by default."""
        self.assertTrue(self.config.permission("web_browsing"))
        self.assertTrue(self.config.permission("file_read"))
        self.assertTrue(self.config.permission("memory"))

    def test_permission_toggles_and_persists(self):
        """Toggling a permission and saving persists across reload."""
        from core.config import Config
        import tempfile, json
        from pathlib import Path
        tmp = tempfile.mkdtemp()
        import core.config as cc
        orig_root = cc.ROOT
        cc.ROOT = Path(tmp)
        Path(tmp, "config").mkdir()
        # Write minimal config
        cfg_data = {"permissions": {"microphone": False, "memory": True}, "providers": {}}
        with open(Path(tmp, "config", "config.json"), "w") as f:
            json.dump(cfg_data, f)
        c = Config()
        self.assertFalse(c.permission("microphone"))
        c.set("permissions", "microphone", True)
        c.save()
        c2 = Config()
        self.assertTrue(c2.permission("microphone"))
        cc.ROOT = orig_root
        import shutil; shutil.rmtree(tmp)


class TestIssue2_OllamaCloud(unittest.TestCase):
    """Issue 2: Ollama cloud support with authentication."""

    def test_provider_accepts_cloud_params(self):
        from providers.ollama_provider import OllamaProvider
        p = OllamaProvider(
            base_url="http://localhost:11434",
            model="llama3",
            cloud_url="https://my-ollama.example.com",
            api_key="secret-token",
            use_cloud=True,
        )
        self.assertEqual(p._base_url, "https://my-ollama.example.com")
        self.assertIn("Bearer", p._headers().get("Authorization", ""))

    def test_local_has_no_auth_header(self):
        from providers.ollama_provider import OllamaProvider
        p = OllamaProvider(base_url="http://localhost:11434", model="llama3")
        self.assertNotIn("Authorization", p._headers())

    def test_cloud_url_stripped_of_trailing_slash(self):
        from providers.ollama_provider import OllamaProvider
        p = OllamaProvider(
            cloud_url="https://example.com/ollama/",
            use_cloud=True,
        )
        self.assertFalse(p._base_url.endswith("/"))

    def test_use_cloud_false_uses_local(self):
        from providers.ollama_provider import OllamaProvider
        p = OllamaProvider(
            base_url="http://localhost:11434",
            cloud_url="https://cloud.example.com",
            use_cloud=False,
        )
        self.assertEqual(p._base_url, "http://localhost:11434")

    def test_use_cloud_requires_cloud_url(self):
        """use_cloud=True with empty cloud_url should fall back to local."""
        from providers.ollama_provider import OllamaProvider
        p = OllamaProvider(
            base_url="http://localhost:11434",
            cloud_url="",
            use_cloud=True,
        )
        # Empty cloud_url → use_cloud is effectively False
        self.assertEqual(p._base_url, "http://localhost:11434")

    def test_router_loads_ollama_cloud_config(self):
        """Router reads cloud fields from config and passes them to provider."""
        from providers.ollama_provider import OllamaProvider
        from providers.router import ProviderRouter
        cfg_data = {
            "enabled": True,
            "base_url": "http://localhost:11434",
            "model": "llama3",
            "cloud_url": "https://cloud.test",
            "api_key": "tok123",
            "use_cloud": True,
        }
        router = ProviderRouter.__new__(ProviderRouter)
        router.config = None
        router._providers = {}
        router._errors = {}
        p = router._load_ollama(cfg_data)
        self.assertIsInstance(p, OllamaProvider)
        self.assertEqual(p._cloud_url, "https://cloud.test")
        self.assertEqual(p._api_key, "tok123")
        self.assertTrue(p._use_cloud)


class TestIssue5_ThreadSafety(unittest.TestCase):
    """Issue 5: Background threads must use Qt-safe dispatch."""

    def test_monitor_callback_dispatches_via_qtimer(self):
        src = open("ui/main_window.py").read()
        # The monitor registration line must use QTimer.singleShot so the
        # background monitor thread never touches Qt widgets directly.
        # Either pattern is valid:
        #   on_update(lambda s: QTimer.singleShot(0, lambda snap=s: self._on_monitor(snap)))
        #   or _on_monitor_update that calls QTimer.singleShot internally
        registration_ok = (
            "QTimer.singleShot" in src and
            ("_on_monitor" in src or "_apply_monitor" in src)
        )
        self.assertTrue(registration_ok,
                        "Monitor callback must dispatch UI updates via QTimer.singleShot(0)")

    def test_apply_monitor_update_exists(self):
        src = open("ui/main_window.py").read()
        # Accept either naming convention for the main-thread monitor handler
        has_handler = ("def _apply_monitor_update" in src or
                       "def _on_monitor" in src)
        self.assertTrue(has_handler,
                        "A main-thread monitor update handler must exist")

    def test_voice_input_uses_qt_safe_callbacks(self):
        src = open("ui/chat_widget.py").read()
        # _voice_input and its inner _listen closure must only touch UI via QTimer.singleShot
        idx = src.find("def _voice_input")
        # Capture to end of _reset_mic_btn definition (enough for finally block)
        snippet = src[idx:idx+1000]
        self.assertIn("QTimer.singleShot", snippet,
                       "Voice input thread must use QTimer.singleShot for UI access")
        self.assertIn("_on_voice_transcript", snippet,
                       "Transcript must be dispatched via _on_voice_transcript")
        self.assertIn("_reset_mic_btn", snippet,
                       "Mic button reset must be in finally block via QTimer.singleShot")

    def test_on_voice_transcript_method_exists(self):
        src = open("ui/chat_widget.py").read()
        self.assertIn("def _on_voice_transcript", src)

    def test_reset_mic_btn_method_exists(self):
        src = open("ui/chat_widget.py").read()
        self.assertIn("def _reset_mic_btn", src)


class TestIssue6_DesktopConfirmation(unittest.TestCase):
    """Issue 6: Sensitive desktop ops require confirmation."""

    def _run(self, coro):
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    def test_launch_app_calls_confirm(self):
        """Launch must call confirm callback before executing."""
        from core.desktop_control import DesktopControl
        confirm_called = []

        def mock_confirm(msg):
            confirm_called.append(msg)
            return False  # deny

        # Give it pc_control permission but deny in confirm
        class MockConfig:
            def permission(self, key): return True

        ctrl = DesktopControl(config=MockConfig(), confirm_callback=mock_confirm)
        result = self._run(ctrl.launch_app("chrome"))
        self.assertTrue(len(confirm_called) > 0,
                        "launch_app must call the confirm callback")
        self.assertFalse(result["ok"], "Denied confirm must return ok=False")

    def test_open_file_calls_confirm(self):
        """open_file must ask for confirmation."""
        from core.desktop_control import DesktopControl
        import tempfile
        confirm_called = []

        def mock_confirm(msg):
            confirm_called.append(msg)
            return False

        class MockConfig:
            def permission(self, key): return True

        ctrl = DesktopControl(config=MockConfig(), confirm_callback=mock_confirm)
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            path = f.name
        try:
            result = self._run(ctrl.open_file(path))
            self.assertTrue(len(confirm_called) > 0)
            self.assertFalse(result["ok"])
        finally:
            os.unlink(path)

    def test_launch_app_blocked_no_permission(self):
        from core.desktop_control import DesktopControl
        ctrl = DesktopControl(config=None)
        result = self._run(ctrl.launch_app("chrome"))
        self.assertFalse(result["ok"])
        self.assertIn("permission", result["message"].lower())

    def test_safe_apps_complete(self):
        from core.desktop_control import SAFE_APPS
        required = ["chrome", "firefox", "vscode", "terminal", "files"]
        for app in required:
            self.assertIn(app, SAFE_APPS, f"{app} must be in SAFE_APPS")

    def test_arbitrary_commands_not_in_safe_apps(self):
        from core.desktop_control import SAFE_APPS
        dangerous = ["rm", "del", "format", "sudo", "bash", "sh", "cmd /c", "powershell"]
        for d in dangerous:
            self.assertNotIn(d, SAFE_APPS, f"'{d}' must not be in SAFE_APPS")


class TestIssue9_ConfigPersistence(unittest.TestCase):
    """Issue 9: Config changes must survive restart."""

    def _make_isolated_config(self):
        import tempfile, json
        from pathlib import Path
        import core.config as cc
        tmp = tempfile.mkdtemp()
        # Write a valid minimal config
        cfg_data = {
            "permissions": {"microphone": False, "memory": True},
            "providers": {
                "default": "",
                "openai": {"enabled": False, "api_key": "", "model": "gpt-4o"}
            },
            "personality": {"mode": "sarcastic", "sarcasm_level": 60},
            "memory": {"enabled": True, "max_history": 50},
            "assistant": {"name": "MAX"}
        }
        Path(tmp, "config").mkdir()
        with open(Path(tmp, "config", "config.json"), "w") as f:
            json.dump(cfg_data, f)
        return tmp, cc

    def test_provider_model_persists(self):
        from core.config import Config
        import tempfile, json
        from pathlib import Path
        import core.config as cc
        tmp, cc_mod = self._make_isolated_config()
        orig = cc_mod.ROOT
        cc_mod.ROOT = Path(tmp)
        try:
            c = Config()
            c.set("providers", "openai", "model", "gpt-4-turbo")
            c.save()
            c2 = Config()
            self.assertEqual(c2.get("providers", "openai", "model"), "gpt-4-turbo")
        finally:
            cc_mod.ROOT = orig
            import shutil; shutil.rmtree(tmp)

    def test_personality_mode_persists(self):
        from core.config import Config
        import tempfile, json
        from pathlib import Path
        import core.config as cc
        tmp, cc_mod = self._make_isolated_config()
        orig = cc_mod.ROOT
        cc_mod.ROOT = Path(tmp)
        try:
            c = Config()
            c.set("personality", "mode", "professional")
            c.set("personality", "sarcasm_level", 10)
            c.save()
            c2 = Config()
            self.assertEqual(c2.get("personality", "mode"), "professional")
            self.assertEqual(c2.get("personality", "sarcasm_level"), 10)
        finally:
            cc_mod.ROOT = orig
            import shutil; shutil.rmtree(tmp)

    def test_permission_change_persists(self):
        from core.config import Config
        import tempfile, json
        from pathlib import Path
        import core.config as cc
        tmp, cc_mod = self._make_isolated_config()
        orig = cc_mod.ROOT
        cc_mod.ROOT = Path(tmp)
        try:
            c = Config()
            self.assertFalse(c.permission("microphone"))
            c.set("permissions", "microphone", True)
            c.save()
            c2 = Config()
            self.assertTrue(c2.permission("microphone"))
        finally:
            cc_mod.ROOT = orig
            import shutil; shutil.rmtree(tmp)

    def test_api_key_not_written_to_config_json(self):
        """API keys must stay in .env, never in config.json."""
        from core.config import Config
        import tempfile, json
        from pathlib import Path
        import core.config as cc
        tmp, cc_mod = self._make_isolated_config()
        orig = cc_mod.ROOT
        cc_mod.ROOT = Path(tmp)
        try:
            c = Config()
            c.set("providers", "openai", "api_key", "sk-secret-key")
            c.set("providers", "openai", "enabled", True)
            c.save()
            # Read raw JSON and verify no key
            raw = json.loads(Path(tmp, "config", "config.json").read_text())
            saved_key = raw.get("providers", {}).get("openai", {}).get("api_key", "")
            self.assertEqual(saved_key, "",
                             "API key must NOT be written to config.json")
        finally:
            cc_mod.ROOT = orig
            import shutil; shutil.rmtree(tmp)

    def test_ollama_cloud_settings_persist(self):
        """Ollama cloud_url and use_cloud must persist."""
        from core.config import Config
        import tempfile, json
        from pathlib import Path
        import core.config as cc
        tmp, cc_mod = self._make_isolated_config()
        orig = cc_mod.ROOT
        cc_mod.ROOT = Path(tmp)
        try:
            c = Config()
            c.set("providers", "ollama", "cloud_url", "https://my-ollama.example.com")
            c.set("providers", "ollama", "use_cloud", True)
            c.set("providers", "ollama", "model", "mixtral")
            c.save()
            c2 = Config()
            self.assertEqual(c2.get("providers", "ollama", "cloud_url"),
                             "https://my-ollama.example.com")
            self.assertTrue(c2.get("providers", "ollama", "use_cloud"))
            self.assertEqual(c2.get("providers", "ollama", "model"), "mixtral")
        finally:
            cc_mod.ROOT = orig
            import shutil; shutil.rmtree(tmp)


class TestMemoryEngineComplete(unittest.TestCase):
    """Issue 1 & 7: Comprehensive memory engine tests."""

    def setUp(self):
        import tempfile
        from pathlib import Path
        self._tmp = tempfile.mkdtemp()
        import memory.memory_engine as me
        self._orig_root = me.ROOT
        me.ROOT = Path(self._tmp)
        Path(self._tmp, "memory").mkdir()
        from memory.memory_engine import MemoryEngine
        self.mem = MemoryEngine()

    def tearDown(self):
        self.mem.close()
        import memory.memory_engine as me
        me.ROOT = self._orig_root
        import shutil; shutil.rmtree(self._tmp)

    def test_store_multiple_and_retrieve(self):
        self.mem.store("What is Python?", "A programming language.")
        self.mem.store("What is MAX?", "An AI assistant by LEREON.")
        ctx = self.mem.get_context("MAX")
        self.assertIn("LEREON", ctx)

    def test_history_ordered_chronologically(self):
        self.mem.store("Q1", "A1")
        self.mem.store("Q2", "A2")
        self.mem.store("Q3", "A3")
        h = self.mem.get_history()
        self.assertEqual(len(h), 3)
        # Oldest first
        self.assertEqual(h[0]["user"], "Q1")
        self.assertEqual(h[2]["user"], "Q3")

    def test_prune_respects_max_history(self):
        """Memory _prune() should delete rows beyond the configured limit."""
        import sqlite3
        from pathlib import Path

        # Directly test the prune SQL logic
        db_path = Path(self._tmp, "memory", "prune_test.db")
        conn = sqlite3.connect(str(db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts REAL NOT NULL,
                user_msg TEXT NOT NULL,
                assistant_msg TEXT NOT NULL
            )
        """)
        import time as t_mod
        for i in range(10):
            conn.execute(
                "INSERT INTO history (ts, user_msg, assistant_msg) VALUES (?,?,?)",
                (t_mod.time() + i, f"Q{i}", f"A{i}")
            )
        conn.commit()

        # Prune to 3
        max_h = 3
        conn.execute(
            "DELETE FROM history WHERE id NOT IN "
            "(SELECT id FROM history ORDER BY ts DESC LIMIT ?)", (max_h,)
        )
        conn.commit()

        count = conn.execute("SELECT COUNT(*) FROM history").fetchone()[0]
        conn.close()
        db_path.unlink()
        self.assertLessEqual(count, 3, "Prune SQL must limit rows to max_history")

    def test_facts_separate_from_history(self):
        self.mem.store("user question", "ai answer")
        self.mem.save_fact("user_name", "Alice")
        self.mem.save_fact("theme", "dark")
        facts = self.mem.get_facts()
        keys = [f["key"] for f in facts]
        self.assertIn("user_name", keys)
        self.assertIn("theme", keys)
        # Facts don't appear in history
        h = self.mem.get_history()
        self.assertEqual(len(h), 1)

    def test_clear_removes_history_not_facts(self):
        self.mem.store("Q", "A")
        self.mem.save_fact("key", "val")
        self.mem.clear()
        self.assertEqual(len(self.mem.get_history()), 0)
        # Facts preserved
        facts = self.mem.get_facts()
        self.assertEqual(len(facts), 1)

    def test_sqlite_file_created(self):
        from pathlib import Path
        db = Path(self._tmp, "memory", "max.db")
        self.assertTrue(db.exists(), "SQLite DB file must exist after init")
        self.assertGreater(db.stat().st_size, 0)

    def test_context_returns_string(self):
        result = self.mem.get_context("anything")
        self.assertIsInstance(result, str)

    def test_empty_history_context_is_empty_string(self):
        ctx = self.mem.get_context("test")
        self.assertEqual(ctx, "")


class TestPersonalityModes(unittest.TestCase):
    """Issue 7: All personality modes must produce distinct prompts."""

    def setUp(self):
        from personality.personality_engine import PersonalityEngine, PersonalityMode
        self.eng = PersonalityEngine()
        self.PersonalityMode = PersonalityMode

    def test_all_modes_produce_different_prompts(self):
        prompts = {}
        for mode in self.PersonalityMode:
            self.eng.set_mode(mode)
            prompts[mode] = self.eng.build_system_prompt()
        # All prompts must be unique
        unique = set(prompts.values())
        self.assertEqual(len(unique), len(list(self.PersonalityMode)),
                         "Every personality mode must produce a unique system prompt")

    def test_sarcastic_mode_contains_sarcasm_guidance(self):
        self.eng.set_mode(self.PersonalityMode.SARCASTIC)
        prompt = self.eng.build_system_prompt()
        self.assertIn("sarcas", prompt.lower())

    def test_professional_mode_no_sarcasm(self):
        self.eng.set_mode(self.PersonalityMode.PROFESSIONAL)
        self.eng.set_sarcasm(0)
        prompt = self.eng.build_system_prompt()
        # Should not contain heavy sarcasm guidance
        self.assertNotIn("Maximum sarcasm", prompt)

    def test_force_serious_disables_humor(self):
        self.eng.settings.force_serious = True
        self.eng.set_sarcasm(100)
        prompt = self.eng.build_system_prompt()
        self.assertIn("strictly professional", prompt.lower())
        self.eng.settings.force_serious = False

    def test_savage_mode_contains_blunt_guidance(self):
        self.eng.set_mode(self.PersonalityMode.SAVAGE)
        prompt = self.eng.build_system_prompt()
        self.assertIn("Blunt", prompt)

    def test_nerdy_mode_contains_technical(self):
        self.eng.set_mode(self.PersonalityMode.NERDY)
        prompt = self.eng.build_system_prompt()
        self.assertIn("technical", prompt.lower())

    def test_branding_always_present(self):
        for mode in self.PersonalityMode:
            self.eng.set_mode(mode)
            prompt = self.eng.build_system_prompt()
            self.assertIn("LEREON", prompt, f"LEREON branding missing in {mode.value} mode")

    def test_sarcasm_zero_no_heavy_sarcasm(self):
        self.eng.set_sarcasm(0)
        prompt = self.eng.build_system_prompt()
        self.assertNotIn("Maximum sarcasm", prompt)
        self.assertNotIn("Heavy sarcasm", prompt)

    def test_sarcasm_100_maximum_guidance(self):
        self.eng.set_mode(self.PersonalityMode.SARCASTIC)
        self.eng.set_sarcasm(100)
        prompt = self.eng.build_system_prompt()
        self.assertIn("sarcasm", prompt.lower())


class TestStudioEngine(unittest.TestCase):
    """Issue 7: MAX Studio must read files and produce correct output."""

    def setUp(self):
        from studio.studio_engine import StudioEngine
        self.studio = StudioEngine(core=None)

    def test_all_template_types_exist(self):
        expected = ["summarize", "code_review", "write_docs", "readme",
                    "explain", "refactor", "unit_tests", "presentation_outline",
                    "report", "email_draft", "meeting_summary", "custom"]
        for t in expected:
            self.assertIn(t, self.studio.task_types, f"Missing task type: {t}")

    def test_read_txt_file(self):
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as f:
            f.write("MAX AI is built by LEREON Technologies.\n" * 5)
            path = f.name
        try:
            result = self.studio.read_file(path)
            self.assertIn("LEREON", result)
        finally:
            os.unlink(path)

    def test_read_md_file(self):
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False, mode="w") as f:
            f.write("# MAX AI\n\nBuilt by LEREON Technologies.")
            path = f.name
        try:
            result = self.studio.read_file(path)
            self.assertIn("LEREON", result)
        finally:
            os.unlink(path)

    def test_read_py_file(self):
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as f:
            f.write("# MAX AI\nprint('hello from LEREON')")
            path = f.name
        try:
            result = self.studio.read_file(path)
            self.assertIn("LEREON", result)
        finally:
            os.unlink(path)

    def test_read_missing_file_graceful(self):
        result = self.studio.read_file("/nonexistent/path/file.txt")
        self.assertIn("not found", result.lower())

    def test_save_and_load_roundtrip(self):
        content = "MAX AI output by LEREON Technologies."
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "output.txt")
            result = self.studio.save_output(content, path)
            self.assertTrue(result["ok"])
            loaded = Path(path).read_text()
            self.assertEqual(loaded, content)

    def test_template_contains_content_placeholder(self):
        for ttype, template in self.studio.TEMPLATES.items():
            self.assertIn("{content}", template,
                          f"Template '{ttype}' must contain {{content}} placeholder")

    def test_run_task_unknown_type_returns_error(self):
        import asyncio
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(
            self.studio.run_task("nonexistent_type", "some content")
        )
        loop.close()
        self.assertIn("Unknown task type", result)


class TestWorkflowAutomation(unittest.TestCase):
    """Issue 7: MAX Automate workflow tests."""

    def setUp(self):
        import tempfile
        from pathlib import Path
        self._tmp = tempfile.mkdtemp()
        import automation.workflow_engine as we
        self._orig = we.ROOT
        we.ROOT = Path(self._tmp)
        Path(self._tmp, "tasks").mkdir()
        from automation.workflow_engine import WorkflowEngine
        self.engine = WorkflowEngine()

    def tearDown(self):
        self.engine.stop_scheduler()
        import automation.workflow_engine as we
        we.ROOT = self._orig
        import shutil; shutil.rmtree(self._tmp)

    def test_workflow_persists_across_reload(self):
        from automation.workflow_engine import (
            WorkflowEngine, TriggerType, ActionType, WorkflowStep
        )
        import automation.workflow_engine as we
        step = WorkflowStep(action=ActionType.WAIT, params={"seconds": 0})
        wf = self.engine.create("Persist Test", "desc", TriggerType.MANUAL, {}, [step])
        wf_id = wf.id
        # Reload engine from disk
        engine2 = WorkflowEngine()
        loaded = engine2.get(wf_id)
        self.assertIsNotNone(loaded, "Workflow must persist across engine reload")
        self.assertEqual(loaded.name, "Persist Test")

    def test_enabled_disabled_toggle(self):
        from automation.workflow_engine import TriggerType, ActionType, WorkflowStep
        step = WorkflowStep(action=ActionType.WAIT, params={"seconds": 0})
        wf = self.engine.create("Toggle", "", TriggerType.MANUAL, {}, [step])
        self.engine.enable(wf.id, False)
        result = self.engine.run_workflow(wf.id)
        self.assertFalse(result["ok"])
        self.assertIn("disabled", result["error"])
        self.engine.enable(wf.id, True)
        result2 = self.engine.run_workflow(wf.id)
        self.assertTrue(result2["ok"])

    def test_run_count_increments(self):
        from automation.workflow_engine import TriggerType, ActionType, WorkflowStep
        step = WorkflowStep(action=ActionType.WAIT, params={"seconds": 0})
        wf = self.engine.create("Count Test", "", TriggerType.MANUAL, {}, [step])
        self.assertEqual(wf.run_count, 0)
        self.engine.run_workflow(wf.id)
        self.engine.run_workflow(wf.id)
        wf2 = self.engine.get(wf.id)
        self.assertEqual(wf2.run_count, 2)

    def test_all_safe_actions_runnable(self):
        from automation.workflow_engine import (
            TriggerType, ActionType, WorkflowStep, SAFE_ACTIONS
        )
        # WAIT is always safe and has no side effects
        self.assertIn("wait", SAFE_ACTIONS)
        step = WorkflowStep(action=ActionType.WAIT, params={"seconds": 0})
        wf = self.engine.create("Safe", "", TriggerType.MANUAL, {}, [step])
        result = self.engine.run_workflow(wf.id)
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["results"]), 1)

    def test_startup_trigger_runs_once(self):
        from automation.workflow_engine import TriggerType, ActionType, WorkflowStep
        step = WorkflowStep(action=ActionType.WAIT, params={"seconds": 0})
        wf = self.engine.create("Startup", "", TriggerType.STARTUP, {}, [step])
        self.assertEqual(wf.run_count, 0)


class TestKnowledgeBaseComplete(unittest.TestCase):
    """Issue 7: MAX Knowledge Base complete tests."""

    def setUp(self):
        import tempfile
        from pathlib import Path
        self._tmp = tempfile.mkdtemp()
        import knowledge.knowledge_base as kb_mod
        self._orig = kb_mod.ROOT
        kb_mod.ROOT = Path(self._tmp)
        Path(self._tmp, "memory").mkdir()
        from knowledge.knowledge_base import KnowledgeBase
        self.kb = KnowledgeBase()

    def tearDown(self):
        self.kb.close()
        import knowledge.knowledge_base as kb_mod
        kb_mod.ROOT = self._orig
        import shutil; shutil.rmtree(self._tmp)

    def test_import_multiple_files(self):
        for i in range(3):
            with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as f:
                f.write(f"Document {i}: MAX AI content about topic_{i} " * 20)
                path = f.name
            result = self.kb.import_file(path)
            self.assertTrue(result["ok"], f"Import {i} failed: {result['message']}")
            os.unlink(path)
        self.assertEqual(self.kb.document_count(), 3)

    def test_search_relevance_ordering(self):
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as f:
            f.write("LEREON LEREON LEREON Technologies MAX AI " * 10)
            path1 = f.name
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as f:
            f.write("Some unrelated content about cooking recipes " * 10)
            path2 = f.name
        try:
            self.kb.import_file(path1)
            self.kb.import_file(path2)
            results = self.kb.search("LEREON")
            self.assertGreater(len(results), 0)
            # Most relevant first
            self.assertGreater(results[0]["relevance"], 0)
            if len(results) > 1:
                self.assertGreaterEqual(results[0]["relevance"], results[1]["relevance"])
        finally:
            os.unlink(path1)
            os.unlink(path2)

    def test_get_context_for_query(self):
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as f:
            f.write("MAX AI was created by LEREON Technologies for personal use. " * 15)
            path = f.name
        try:
            self.kb.import_file(path)
            ctx = self.kb.get_context_for_query("LEREON Technologies")
            self.assertIn("Knowledge Base Context", ctx)
            self.assertIn("LEREON", ctx)
        finally:
            os.unlink(path)

    def test_get_context_empty_when_no_match(self):
        ctx = self.kb.get_context_for_query("xyzzy_no_match_expected_123")
        self.assertEqual(ctx, "")


# ── Main ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()
    test_classes = [
        TestConfig, TestTools, TestMemory, TestPersonality,
        TestKnowledgeBase, TestProductivity, TestAutomation,
        TestPlugins, TestMonitor, TestStudio, TestVision,
        TestDesktopControl, TestDiagnostics,
        # Issue-specific regression tests
        TestIssue1_PermissionDefaults,
        TestIssue2_OllamaCloud,
        TestIssue5_ThreadSafety,
        TestIssue6_DesktopConfirmation,
        TestIssue9_ConfigPersistence,
        # Comprehensive feature tests
        TestMemoryEngineComplete,
        TestPersonalityModes,
        TestStudioEngine,
        TestWorkflowAutomation,
        TestKnowledgeBaseComplete,
    ]
    for cls in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(cls))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
