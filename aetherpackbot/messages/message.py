"""Message types and content models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any
from uuid import uuid4


class MessageType(Enum):
    """Types of message content."""

    TEXT = auto()
    IMAGE = auto()
    AUDIO = auto()
    VIDEO = auto()
    FILE = auto()
    LOCATION = auto()
    CONTACT = auto()
    STICKER = auto()
    UNKNOWN = auto()


@dataclass
class TextContent:
    """Text message content."""

    text: str
    entities: list[dict[str, Any]] = field(default_factory=list)

    @property
    def type(self) -> MessageType:
        return MessageType.TEXT


@dataclass
class ImageContent:
    """Image message content."""

    url: str | None = None
    file_id: str | None = None
    data: bytes | None = None
    mime_type: str = "image/jpeg"
    width: int | None = None
    height: int | None = None
    caption: str | None = None

    @property
    def type(self) -> MessageType:
        return MessageType.IMAGE


@dataclass
class AudioContent:
    """Audio message content."""

    url: str | None = None
    file_id: str | None = None
    data: bytes | None = None
    mime_type: str = "audio/mpeg"
    duration: int | None = None
    title: str | None = None

    @property
    def type(self) -> MessageType:
        return MessageType.AUDIO


@dataclass
class VideoContent:
    """Video message content."""

    url: str | None = None
    file_id: str | None = None
    data: bytes | None = None
    mime_type: str = "video/mp4"
    width: int | None = None
    height: int | None = None
    duration: int | None = None
    caption: str | None = None

    @property
    def type(self) -> MessageType:
        return MessageType.VIDEO


@dataclass
class FileContent:
    """File/document message content."""

    url: str | None = None
    file_id: str | None = None
    data: bytes | None = None
    filename: str = "file"
    mime_type: str = "application/octet-stream"
    size: int | None = None

    @property
    def type(self) -> MessageType:
        return MessageType.FILE


ContentType = TextContent | ImageContent | AudioContent | VideoContent | FileContent


@dataclass
class Message:
    """Universal message representation across platforms."""

    id: str = field(default_factory=lambda: uuid4().hex[:16])
    content: ContentType = field(default_factory=lambda: TextContent(text=""))
    chat_id: str = ""
    sender_id: str | None = None
    reply_to_id: str | None = None
    thread_id: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    platform_data: dict[str, Any] = field(default_factory=dict)

    @property
    def type(self) -> MessageType:
        """Get the message type based on content."""
        return self.content.type

    @property
    def text(self) -> str:
        """Get text content if available."""
        if isinstance(self.content, TextContent):
            return self.content.text
        return ""

    @classmethod
    def text_message(cls, text: str, chat_id: str = "", **kwargs: Any) -> Message:
        """Create a text message."""
        return cls(content=TextContent(text=text), chat_id=chat_id, **kwargs)

    @classmethod
    def image_message(
        cls, url: str | None = None, data: bytes | None = None, **kwargs: Any
    ) -> Message:
        """Create an image message."""
        return cls(content=ImageContent(url=url, data=data), **kwargs)

    def with_reply(self, message_id: str) -> Message:
        """Create a copy of this message as a reply."""
        self.reply_to_id = message_id
        return self
