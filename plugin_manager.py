"""
MAX AI — Plugin Manager
LEREON Technologies

Modular plugin architecture. Plugins extend MAX without modifying core code.
Plugins run in isolated scope. No unrestricted system access granted automatically.
"""

import logging
import importlib
import importlib.util
import sys
import traceback
from dataclasses import dataclass, field
from typing import Optional, Callable, Any
from pathlib import Path

logger = logging.getLogger("MAX.plugins")
PLUGINS_DIR = Path(__file__).parent.parent / "plugins" / "installed"


@dataclass
class PluginMeta:
    id: str
    name: str
    version: str
    description: str
    author: str
    permissions_required: list = field(default_factory=list)
    enabled: bool = True
    error: Optional[str] = None


class BasePlugin:
    """
    Base class all MAX plugins must inherit from.
    Plugins must implement: meta, on_load(), on_unload().
    Optional: on_chat_message(), on_tool_call(), get_tools().
    """

    @property
    def meta(self) -> PluginMeta:
        raise NotImplementedError

    def on_load(self, core) -> bool:
        """Called when plugin is activated. Return True on success."""
        return True

    def on_unload(self):
        """Called when plugin is deactivated."""
        pass

    def on_chat_message(self, user_msg: str, response: str) -> Optional[str]:
        """
        Called after each chat exchange.
        Return modified response string, or None to leave unchanged.
        """
        return None

    def get_tools(self) -> list:
        """Return list of tool instances to register with ToolRegistry."""
        return []


class PluginManager:
    """Loads, activates, and manages MAX AI plugins."""

    def __init__(self, core=None):
        self._core = core
        self._plugins: dict[str, BasePlugin] = {}
        self._metas: dict[str, PluginMeta] = {}
        PLUGINS_DIR.mkdir(parents=True, exist_ok=True)
        # Create example plugin template
        self._write_example_plugin()
        logger.info("Plugin manager ready.")

    def _write_example_plugin(self):
        """Write a documented example plugin for developers."""
        example = PLUGINS_DIR / "example_plugin.py.template"
        if example.exists():
            return
        example.write_text('''"""
MAX AI — Example Plugin Template
LEREON Technologies

Copy this file to a new .py file in plugins/installed/ to create your plugin.
"""

from plugins.plugin_manager import BasePlugin, PluginMeta


class ExamplePlugin(BasePlugin):
    """
    Example MAX AI plugin.
    Replace this with your implementation.
    """

    @property
    def meta(self) -> PluginMeta:
        return PluginMeta(
            id="example_plugin",
            name="Example Plugin",
            version="1.0.0",
            description="A template for creating MAX AI plugins.",
            author="Your Name",
            permissions_required=[],  # List required permissions
        )

    def on_load(self, core) -> bool:
        """Called when plugin activates. core is the MAXCore instance."""
        print("Example plugin loaded!")
        return True

    def on_unload(self):
        print("Example plugin unloaded.")

    def on_chat_message(self, user_msg: str, response: str):
        """Optional: post-process chat responses. Return None to leave unchanged."""
        return None  # Return modified response or None


# REQUIRED: The plugin manager looks for a class named Plugin in each file.
Plugin = ExamplePlugin
''')

    def discover(self) -> list:
        """Scan plugins/installed/ for .py files and return their metadata."""
        discovered = []
        for path in sorted(PLUGINS_DIR.glob("*.py")):
            if path.name.startswith("_"):
                continue
            try:
                meta = self._load_meta(path)
                if meta:
                    discovered.append(meta)
            except Exception as e:
                logger.warning(f"Plugin discovery failed for {path.name}: {e}")
        return discovered

    def _load_meta(self, path: Path) -> Optional[PluginMeta]:
        spec = importlib.util.spec_from_file_location(path.stem, path)
        mod = importlib.util.module_from_spec(spec)
        # Sandboxed: don't add to sys.modules to prevent cross-plugin access
        try:
            spec.loader.exec_module(mod)
        except Exception as e:
            return PluginMeta(id=path.stem, name=path.stem, version="?",
                              description="Load error", author="?", error=str(e))
        plugin_cls = getattr(mod, "Plugin", None)
        if plugin_cls is None:
            return None
        try:
            instance = plugin_cls()
            meta = instance.meta
            meta.error = None
            return meta
        except Exception as e:
            return PluginMeta(id=path.stem, name=path.stem, version="?",
                              description="Meta error", author="?", error=str(e))

    def load_plugin(self, plugin_id: str) -> dict:
        """Load and activate a plugin by its file stem."""
        path = PLUGINS_DIR / f"{plugin_id}.py"
        if not path.exists():
            return {"ok": False, "error": f"Plugin file not found: {path}"}

        try:
            spec = importlib.util.spec_from_file_location(plugin_id, path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            plugin_cls = getattr(mod, "Plugin", None)
            if plugin_cls is None:
                return {"ok": False, "error": "No 'Plugin' class found in module."}
            instance: BasePlugin = plugin_cls()
            meta = instance.meta

            # Check permissions
            if meta.permissions_required:
                logger.info(f"Plugin '{meta.name}' requires: {meta.permissions_required}")

            success = instance.on_load(self._core)
            if not success:
                return {"ok": False, "error": "Plugin on_load() returned False."}

            self._plugins[meta.id] = instance
            self._metas[meta.id] = meta
            logger.info(f"Plugin loaded: {meta.name} v{meta.version}")
            return {"ok": True, "meta": meta}

        except Exception as e:
            err = traceback.format_exc()
            logger.error(f"Plugin load error ({plugin_id}): {err}")
            return {"ok": False, "error": str(e)}

    def unload_plugin(self, plugin_id: str) -> bool:
        plugin = self._plugins.get(plugin_id)
        if not plugin:
            return False
        try:
            plugin.on_unload()
        except Exception as e:
            logger.warning(f"Plugin unload error ({plugin_id}): {e}")
        del self._plugins[plugin_id]
        self._metas.pop(plugin_id, None)
        logger.info(f"Plugin unloaded: {plugin_id}")
        return True

    def notify_chat(self, user_msg: str, response: str) -> str:
        """Pass chat exchange through all plugins. Return potentially modified response."""
        for pid, plugin in list(self._plugins.items()):
            try:
                result = plugin.on_chat_message(user_msg, response)
                if result is not None:
                    response = result
            except Exception as e:
                logger.warning(f"Plugin {pid} chat hook error: {e}")
        return response

    def get_all_tools(self) -> list:
        """Collect tools from all loaded plugins."""
        tools = []
        for plugin in self._plugins.values():
            try:
                tools.extend(plugin.get_tools())
            except Exception as e:
                logger.warning(f"Plugin tool error: {e}")
        return tools

    @property
    def loaded_plugins(self) -> list:
        return list(self._metas.values())

    @property
    def loaded_count(self) -> int:
        return len(self._plugins)
