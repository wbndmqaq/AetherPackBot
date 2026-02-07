"""Base LLM provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ChatRole(str, Enum):
    """Chat message roles."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class ChatMessage:
    """Chat message for LLM conversation."""

    role: ChatRole
    content: str
    name: str | None = None
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None


@dataclass
class LLMConfig:
    """Base configuration for LLM providers."""

    name: str
    api_key: str = ""
    model: str = ""
    base_url: str | None = None
    timeout: int = 60
    max_tokens: int = 4096
    temperature: float = 0.7
    options: dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    """Response from LLM provider."""

    content: str
    model: str
    finish_reason: str | None = None
    usage: dict[str, int] | None = None
    tool_calls: list[dict[str, Any]] | None = None
    raw_response: Any = None


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    name: str = "base"

    def __init__(self, config: LLMConfig) -> None:
        self.config = config
        self._client: Any = None

    @abstractmethod
    async def chat(
        self,
        messages: list[ChatMessage],
        **kwargs: Any,
    ) -> LLMResponse:
        """Send chat completion request."""
        ...

    @abstractmethod
    async def chat_stream(
        self,
        messages: list[ChatMessage],
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream chat completion response."""
        ...

    async def complete(self, prompt: str, **kwargs: Any) -> str:
        """Simple text completion."""
        messages = [ChatMessage(role=ChatRole.USER, content=prompt)]
        response = await self.chat(messages, **kwargs)
        return response.content

    def count_tokens(self, text: str) -> int:
        """Estimate token count for text. Override for accurate counting."""
        # Simple estimation: ~4 chars per token
        return len(text) // 4

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} model={self.config.model}>"
