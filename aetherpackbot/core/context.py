"""Context object for request/response handling."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any
from uuid import uuid4

if TYPE_CHECKING:
    from aetherpackbot.messages.message import Message
    from aetherpackbot.platforms.base import Platform


@dataclass
class User:
    """Represents a user across platforms."""

    id: str
    platform_id: str
    username: str | None = None
    display_name: str | None = None
    is_bot: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Chat:
    """Represents a chat/conversation context."""

    id: str
    platform_id: str
    type: str = "private"  # private, group, channel
    title: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Context:
    """Request context carrying all information about a message interaction."""

    id: str = field(default_factory=lambda: uuid4().hex[:16])
    message: Message | None = None
    user: User | None = None
    chat: Chat | None = None
    platform: Platform | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # State management
    _state: dict[str, Any] = field(default_factory=dict)
    _responses: list[Message] = field(default_factory=list)

    def set(self, key: str, value: Any) -> None:
        """Store a value in context state."""
        self._state[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a value from context state."""
        return self._state.get(key, default)

    def has(self, key: str) -> bool:
        """Check if a key exists in state."""
        return key in self._state

    async def reply(self, content: str, **kwargs: Any) -> Message | None:
        """Send a reply to the current chat."""
        if self.platform and self.chat:
            from aetherpackbot.messages.message import Message, TextContent

            msg = Message(
                content=TextContent(text=content),
                chat_id=self.chat.id,
                **kwargs,
            )
            result = await self.platform.send_message(msg)
            if result:
                self._responses.append(result)
            return result
        return None

    async def reply_typing(self) -> None:
        """Send typing indicator."""
        if self.platform and self.chat:
            await self.platform.send_typing(self.chat.id)

    @property
    def text(self) -> str:
        """Get message text content."""
        if self.message and hasattr(self.message.content, "text"):
            return self.message.content.text
        return ""

    @property
    def is_command(self) -> bool:
        """Check if message starts with a command prefix."""
        return self.text.startswith("/")

    @property
    def command(self) -> str | None:
        """Extract command name without prefix."""
        if self.is_command:
            parts = self.text.split()
            if parts:
                return parts[0][1:].lower()
        return None

    @property
    def args(self) -> list[str]:
        """Get command arguments."""
        if self.is_command:
            parts = self.text.split()
            return parts[1:] if len(parts) > 1 else []
        return []
