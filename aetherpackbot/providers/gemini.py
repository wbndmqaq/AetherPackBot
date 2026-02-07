"""Google Gemini LLM provider."""

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
class GeminiConfig(LLMConfig):
    """Gemini-specific configuration."""

    model: str = "gemini-pro"


class GeminiProvider(LLMProvider):
    """Google Gemini API provider."""

    name = "gemini"

    def __init__(self, config: GeminiConfig) -> None:
        super().__init__(config)
        self._model = None

    def _get_model(self) -> Any:
        """Lazy-load Gemini model."""
        if self._model is None:
            try:
                import google.generativeai as genai

                genai.configure(api_key=self.config.api_key)
                self._model = genai.GenerativeModel(self.config.model)
            except ImportError:
                logger.error("gemini_not_installed", hint="pip install google-generativeai")
                raise
        return self._model

    def _convert_messages(self, messages: list[ChatMessage]) -> list[dict[str, Any]]:
        """Convert ChatMessage to Gemini format."""
        history = []

        for msg in messages:
            if msg.role == ChatRole.SYSTEM:
                # System messages are prepended to the first user message
                continue

            role = "user" if msg.role == ChatRole.USER else "model"
            history.append({"role": role, "parts": [msg.content]})

        return history

    async def chat(
        self,
        messages: list[ChatMessage],
        **kwargs: Any,
    ) -> LLMResponse:
        """Send chat completion request."""
        model = self._get_model()
        history = self._convert_messages(messages)

        # Extract last user message
        if not history:
            raise ValueError("No messages provided")

        try:
            chat = model.start_chat(history=history[:-1] if len(history) > 1 else [])
            response = await chat.send_message_async(history[-1]["parts"][0])

            return LLMResponse(
                content=response.text,
                model=self.config.model,
                finish_reason="stop",
                usage={
                    "prompt_tokens": response.usage_metadata.prompt_token_count,
                    "completion_tokens": response.usage_metadata.candidates_token_count,
                }
                if hasattr(response, "usage_metadata")
                else None,
                raw_response=response,
            )
        except Exception:
            logger.exception("gemini_chat_failed")
            raise

    async def chat_stream(
        self,
        messages: list[ChatMessage],
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream chat completion response."""
        model = self._get_model()
        history = self._convert_messages(messages)

        if not history:
            raise ValueError("No messages provided")

        try:
            chat = model.start_chat(history=history[:-1] if len(history) > 1 else [])
            response = await chat.send_message_async(history[-1]["parts"][0], stream=True)

            async for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception:
            logger.exception("gemini_stream_failed")
            raise
