"""OpenAI LLM provider."""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

import structlog

from aetherpackbot.providers.base import (
    ChatMessage,
    LLMConfig,
    LLMProvider,
    LLMResponse,
)

logger = structlog.get_logger(__name__)


@dataclass
class OpenAIConfig(LLMConfig):
    """OpenAI-specific configuration."""

    model: str = "gpt-4"
    organization: str | None = None


class OpenAIProvider(LLMProvider):
    """OpenAI API provider."""

    name = "openai"

    def __init__(self, config: OpenAIConfig) -> None:
        super().__init__(config)
        self._client = None

    def _get_client(self) -> Any:
        """Lazy-load OpenAI client."""
        if self._client is None:
            try:
                from openai import AsyncOpenAI

                self._client = AsyncOpenAI(
                    api_key=self.config.api_key,
                    base_url=self.config.base_url,
                    timeout=self.config.timeout,
                )
            except ImportError:
                logger.error("openai_not_installed", hint="pip install openai")
                raise
        return self._client

    def _convert_messages(self, messages: list[ChatMessage]) -> list[dict[str, Any]]:
        """Convert ChatMessage to OpenAI format."""
        result = []
        for msg in messages:
            m: dict[str, Any] = {"role": msg.role.value, "content": msg.content}
            if msg.name:
                m["name"] = msg.name
            if msg.tool_calls:
                m["tool_calls"] = msg.tool_calls
            if msg.tool_call_id:
                m["tool_call_id"] = msg.tool_call_id
            result.append(m)
        return result

    async def chat(
        self,
        messages: list[ChatMessage],
        **kwargs: Any,
    ) -> LLMResponse:
        """Send chat completion request."""
        client = self._get_client()

        params: dict[str, Any] = {
            "model": kwargs.get("model", self.config.model),
            "messages": self._convert_messages(messages),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "temperature": kwargs.get("temperature", self.config.temperature),
        }

        # Add tools if provided
        if tools := kwargs.get("tools"):
            params["tools"] = tools

        try:
            response = await client.chat.completions.create(**params)
            choice = response.choices[0]

            tool_calls = None
            if choice.message.tool_calls:
                tool_calls = [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in choice.message.tool_calls
                ]

            return LLMResponse(
                content=choice.message.content or "",
                model=response.model,
                finish_reason=choice.finish_reason,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
                if response.usage
                else None,
                tool_calls=tool_calls,
                raw_response=response,
            )
        except Exception:
            logger.exception("openai_chat_failed")
            raise

    async def chat_stream(
        self,
        messages: list[ChatMessage],
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream chat completion response."""
        client = self._get_client()

        params: dict[str, Any] = {
            "model": kwargs.get("model", self.config.model),
            "messages": self._convert_messages(messages),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "temperature": kwargs.get("temperature", self.config.temperature),
            "stream": True,
        }

        try:
            async for chunk in await client.chat.completions.create(**params):
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception:
            logger.exception("openai_stream_failed")
            raise

    def count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken if available."""
        try:
            import tiktoken

            encoding = tiktoken.encoding_for_model(self.config.model)
            return len(encoding.encode(text))
        except ImportError:
            return super().count_tokens(text)
