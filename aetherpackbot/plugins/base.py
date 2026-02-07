"""Base plugin class and metadata."""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from aetherpackbot.core.context import Context
    from aetherpackbot.core.engine import BotEngine


@dataclass
class PluginMeta:
    """Plugin metadata."""

    name: str
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    dependencies: list[str] = field(default_factory=list)
    enabled: bool = True


class Plugin(ABC):
    """Base plugin class. All plugins should inherit from this."""

    meta: PluginMeta = PluginMeta(name="base")
    engine: BotEngine | None = None

    _commands: dict[str, Any] = {}
    _handlers: list[Any] = []
    _event_handlers: dict[type, list[Any]] = {}

    def __init__(self) -> None:
        self._commands = {}
        self._handlers = []
        self._event_handlers = {}

    async def on_load(self) -> None:
        """Called when plugin is loaded. Override for initialization."""
        pass

    async def on_unload(self) -> None:
        """Called when plugin is unloaded. Override for cleanup."""
        pass

    async def on_message(self, context: Context) -> bool:
        """Handle message. Return True to stop propagation."""
        return False

    def register_command(
        self,
        name: str,
        handler: Any,
        description: str = "",
        aliases: list[str] | None = None,
    ) -> None:
        """Register a command handler."""
        self._commands[name] = {
            "handler": handler,
            "description": description,
            "aliases": aliases or [],
        }

    def get_command(self, name: str) -> Any | None:
        """Get command handler by name."""
        if name in self._commands:
            return self._commands[name]["handler"]

        # Check aliases
        for _, cmd_info in self._commands.items():
            if name in cmd_info.get("aliases", []):
                return cmd_info["handler"]

        return None

    @property
    def commands(self) -> dict[str, Any]:
        """Get all registered commands."""
        return self._commands

    def __repr__(self) -> str:
        return f"<Plugin {self.meta.name} v{self.meta.version}>"
