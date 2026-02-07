"""Anthropic Claude LLM provider."""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

import structlog

from aetherpackbot.providers.base import (
    ChatMessage,
    ChatRole,
    LLMConfig,
    LLMProvider,
    LLMResponse,
)

logger = structlog.get_logger(__name__)


@dataclass
class AnthropicConfig(LLMConfig):
    """Anthropic-specific configuration."""

    model: str = "claude-3-opus-20240229"
    max_tokens: int = 4096


class AnthropicProvider(LLMProvider):
    """Anthropic Claude API provider."""

    name = "anthropic"

    def __init__(self, config: AnthropicConfig) -> None:
        super().__init__(config)
        self._client = None

    def _get_client(self) -> Any:
        """Lazy-load Anthropic client."""
        if self._client is None:
            try:
                from anthropic import AsyncAnthropic

                self._client = AsyncAnthropic(
                    api_key=self.config.api_key,
                    timeout=self.config.timeout,
                )
            except ImportError:
                logger.error("anthropic_not_installed", hint="pip install anthropic")
                raise
        return self._client

    def _convert_messages(
        self, messages: list[ChatMessage]
    ) -> tuple[str | None, list[dict[str, Any]]]:
        """Convert ChatMessage to Anthropic format."""
        system_prompt = None
        result = []

        for msg in messages:
            if msg.role == ChatRole.SYSTEM:
                system_prompt = msg.content
                continue

            role = "user" if msg.role == ChatRole.USER else "assistant"
            result.append({"role": role, "content": msg.content})

        return system_prompt, result

    async def chat(
        self,
        messages: list[ChatMessage],
        **kwargs: Any,
    ) -> LLMResponse:
        """Send chat completion request."""
        client = self._get_client()
        system_prompt, converted = self._convert_messages(messages)

        params: dict[str, Any] = {
            "model": kwargs.get("model", self.config.model),
            "messages": converted,
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
        }

        if system_prompt:
            params["system"] = system_prompt

        # Add tools if provided
        if tools := kwargs.get("tools"):
            params["tools"] = self._convert_tools(tools)

        try:
            response = await client.messages.create(**params)

            content = ""
            tool_calls = None

            for block in response.content:
                if block.type == "text":
                    content += block.text
                elif block.type == "tool_use":
                    if tool_calls is None:
                        tool_calls = []
                    tool_calls.append(
                        {
                            "id": block.id,
                            "name": block.name,
                            "input": block.input,
                        }
                    )

            return LLMResponse(
                content=content,
                model=response.model,
                finish_reason=response.stop_reason,
                usage={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                }
                if response.usage
                else None,
                tool_calls=tool_calls,
                raw_response=response,
            )
        except Exception:
            logger.exception("anthropic_chat_failed")
            raise

    async def chat_stream(
        self,
        messages: list[ChatMessage],
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream chat completion response."""
        client = self._get_client()
        system_prompt, converted = self._convert_messages(messages)

        params: dict[str, Any] = {
            "model": kwargs.get("model", self.config.model),
            "messages": converted,
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
        }

        if system_prompt:
            params["system"] = system_prompt

        try:
            async with client.messages.stream(**params) as stream:
                async for text in stream.text_stream:
                    yield text
        except Exception:
            logger.exception("anthropic_stream_failed")
            raise

    def _convert_tools(self, tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Convert OpenAI-style tools to Anthropic format."""
        result = []
        for tool in tools:
            if tool.get("type") == "function":
                func = tool["function"]
                result.append(
                    {
                        "name": func["name"],
                        "description": func.get("description", ""),
                        "input_schema": func.get("parameters", {}),
                    }
                )
        return result
