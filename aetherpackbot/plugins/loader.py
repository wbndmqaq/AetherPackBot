"""Plugin loader for discovering and loading plugins."""

from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import structlog

from aetherpackbot.plugins.base import Plugin

if TYPE_CHECKING:
    from aetherpackbot.core.engine import BotEngine

logger = structlog.get_logger(__name__)


class PluginLoader:
    """Discovers and loads plugins from directories."""

    def __init__(self, engine: BotEngine) -> None:
        self.engine = engine
        self._plugin_dirs: list[Path] = []
        self._loaded: dict[str, Plugin] = {}

    def add_directory(self, path: str | Path) -> None:
        """Add a directory to search for plugins."""
        path = Path(path)
        if path.exists() and path.is_dir():
            self._plugin_dirs.append(path)
            logger.debug("plugin_dir_added", path=str(path))

    def discover(self) -> list[str]:
        """Discover available plugins. Returns list of plugin names."""
        found: list[str] = []

        for plugin_dir in self._plugin_dirs:
            for item in plugin_dir.iterdir():
                if item.is_dir() and (item / "__init__.py").exists():
                    found.append(item.name)
                elif item.is_file() and item.suffix == ".py" and item.stem != "__init__":
                    found.append(item.stem)

        return found

    def load(self, name: str) -> Plugin | None:
        """Load a plugin by name."""
        if name in self._loaded:
            logger.warning("plugin_already_loaded", name=name)
            return self._loaded[name]

        for plugin_dir in self._plugin_dirs:
            # Try as package
            package_path = plugin_dir / name / "__init__.py"
            if package_path.exists():
                return self._load_from_path(name, package_path)

            # Try as module
            module_path = plugin_dir / f"{name}.py"
            if module_path.exists():
                return self._load_from_path(name, module_path)

        logger.error("plugin_not_found", name=name)
        return None

    def _load_from_path(self, name: str, path: Path) -> Plugin | None:
        """Load plugin from file path."""
        try:
            spec = importlib.util.spec_from_file_location(f"aetherpackbot_plugins.{name}", path)
            if not spec or not spec.loader:
                return None

            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)

            # Find Plugin subclass
            plugin_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, Plugin) and attr is not Plugin:
                    plugin_class = attr
                    break

            if not plugin_class:
                logger.error("no_plugin_class", name=name)
                return None

            # Instantiate plugin
            plugin = plugin_class()
            plugin.engine = self.engine
            self._loaded[name] = plugin

            # Register with engine
            self.engine.register_plugin(name, plugin)

            logger.info("plugin_loaded", name=name, version=plugin.meta.version)
            return plugin

        except Exception:
            logger.exception("plugin_load_failed", name=name)
            return None

    def unload(self, name: str) -> bool:
        """Unload a plugin."""
        if name not in self._loaded:
            return False

        self._loaded.pop(name)

        # Remove from sys.modules
        module_name = f"aetherpackbot_plugins.{name}"
        if module_name in sys.modules:
            del sys.modules[module_name]

        logger.info("plugin_unloaded", name=name)
        return True

    def reload(self, name: str) -> Plugin | None:
        """Reload a plugin."""
        self.unload(name)
        return self.load(name)

    @property
    def plugins(self) -> dict[str, Plugin]:
        """Get all loaded plugins."""
        return self._loaded
