import importlib
import os
from pathlib import Path
from utils.logger import get_logger

log = get_logger("plugin_manager")

PLUGINS_DIR = Path(__file__).parent.parent / "plugins"


class Plugin:
    def __init__(self, name, description, category, version="1.0.0", author=""):
        self.name = name
        self.description = description
        self.category = category
        self.version = version
        self.author = author

    def run(self, target, **kwargs):
        raise NotImplementedError


class PluginManager:
    def __init__(self):
        self._plugins = {}
        self._load_plugins()

    def _load_plugins(self):
        if not PLUGINS_DIR.exists():
            return
        for category_dir in PLUGINS_DIR.iterdir():
            if not category_dir.is_dir():
                continue
            category = category_dir.name
            for plugin_file in category_dir.glob("*.py"):
                if plugin_file.name.startswith("_"):
                    continue
                try:
                    module_name = f"plugins.{category}.{plugin_file.stem}"
                    module = importlib.import_module(module_name)
                    if hasattr(module, "plugin"):
                        plugin = module.plugin
                        plugin._category = category
                        key = f"{category}/{plugin.name}"
                        self._plugins[key] = plugin
                        log.info(f"Loaded plugin: {key} v{plugin.version}")
                except Exception as e:
                    log.warning(f"Failed to load plugin {plugin_file}: {e}")

    def list_plugins(self, category=None):
        plugins = []
        for key, plugin in self._plugins.items():
            if category is None or plugin._category == category:
                plugins.append({
                    "name": plugin.name,
                    "description": plugin.description,
                    "category": plugin._category,
                    "version": plugin.version,
                    "author": plugin.author,
                })
        return plugins

    def get_plugin(self, name):
        return self._plugins.get(name)

    def run_plugin(self, name, target, **kwargs):
        plugin = self._plugins.get(name)
        if not plugin:
            return {"error": f"Plugin '{name}' not found"}
        try:
            return plugin.run(target, **kwargs)
        except Exception as e:
            return {"error": str(e)}


_global_manager = None


def get_plugin_manager():
    global _global_manager
    if _global_manager is None:
        _global_manager = PluginManager()
    return _global_manager
