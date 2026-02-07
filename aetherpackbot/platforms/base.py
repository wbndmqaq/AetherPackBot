"""Base platform adapter interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from aetherpackbot.core.context import Context
    from aetherpackbot.core.engine import BotEngine
    from aetherpackbot.messages.message import Message


@dataclass
class PlatformConfig:
    """Base configuration for platforms."""

    name: str
    enabled: bool = True
    options: dict[str, Any] = field(default_factory=dict)


class Platform(ABC):
    """Abstract base class for messaging platform adapters."""

    name: str = "base"
    engine: BotEngine | None = None

    def __init__(self, config: PlatformConfig) -> None:
        self.config = config
        self._connected = False

    @abstractmethod
    async def start(self) -> None:
        """Start the platform connection."""
        ...

    @abstractmethod
    async def stop(self) -> None:
        """Stop the platform connection."""
        ...

    @abstractmethod
    async def send_message(self, message: Message) -> Message | None:
        """Send a message through the platform."""
        ...

    @abstractmethod
    async def send_typing(self, chat_id: str) -> None:
        """Send typing indicator to a chat."""
        ...

    async def on_message(self, context: Context) -> None:
        """Handle incoming message. Override in subclass."""
        pass

    @property
    def is_connected(self) -> bool:
        """Check if platform is connected."""
        return self._connected

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name} connected={self._connected}>"
