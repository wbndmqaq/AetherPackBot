"""Telegram platform adapter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import structlog

from aetherpackbot.core.context import Chat, Context, User
from aetherpackbot.core.events import Event
from aetherpackbot.messages.message import Message, TextContent
from aetherpackbot.platforms.base import Platform, PlatformConfig

logger = structlog.get_logger(__name__)


@dataclass
class TelegramConfig(PlatformConfig):
    """Telegram-specific configuration."""

    token: str = ""
    parse_mode: str = "HTML"
    timeout: int = 30


class TelegramMessageEvent(Event):
    """Event fired when a Telegram message is received."""

    context: Context | None = None


class TelegramPlatform(Platform):
    """Telegram Bot API adapter."""

    name = "telegram"

    def __init__(self, config: TelegramConfig) -> None:
        super().__init__(config)
        self._app = None
        self._token = config.token

    async def start(self) -> None:
        """Start the Telegram bot."""
        try:
            from telegram.ext import Application, MessageHandler, filters

            self._app = Application.builder().token(self._token).build()

            # Register handlers
            self._app.add_handler(
                MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message)
            )
            self._app.add_handler(MessageHandler(filters.COMMAND, self._handle_command))

            await self._app.initialize()
            await self._app.start()
            await self._app.updater.start_polling()

            self._connected = True
            logger.info("telegram_started")

        except ImportError:
            logger.error("telegram_not_installed", hint="pip install python-telegram-bot")
            raise
        except Exception:
            logger.exception("telegram_start_failed")
            raise

    async def stop(self) -> None:
        """Stop the Telegram bot."""
        if self._app:
            await self._app.updater.stop()
            await self._app.stop()
            await self._app.shutdown()
        self._connected = False
        logger.info("telegram_stopped")

    async def _handle_message(self, update: Any, context: Any) -> None:
        """Handle incoming text message."""
        if not update.message:
            return

        msg = update.message
        ctx = self._build_context(msg)

        # Emit event
        if self.engine:
            event = TelegramMessageEvent()
            event.context = ctx
            await self.engine.event_bus.emit(event)

            # Call platform handler
            await self.on_message(ctx)

    async def _handle_command(self, update: Any, context: Any) -> None:
        """Handle command message."""
        await self._handle_message(update, context)

    def _build_context(self, msg: Any) -> Context:
        """Build context from Telegram message."""
        user = User(
            id=str(msg.from_user.id),
            platform_id=f"telegram:{msg.from_user.id}",
            username=msg.from_user.username,
            display_name=msg.from_user.full_name,
            is_bot=msg.from_user.is_bot,
        )

        chat = Chat(
            id=str(msg.chat.id),
            platform_id=f"telegram:{msg.chat.id}",
            type=msg.chat.type,
            title=msg.chat.title or msg.chat.full_name,
        )

        message = Message(
            id=str(msg.message_id),
            content=TextContent(text=msg.text or ""),
            chat_id=str(msg.chat.id),
            sender_id=str(msg.from_user.id),
            platform_data={"telegram_message": msg},
        )

        return Context(
            message=message,
            user=user,
            chat=chat,
            platform=self,
        )

    async def send_message(self, message: Message) -> Message | None:
        """Send a message to Telegram."""
        if not self._app or not message.chat_id:
            return None

        try:
            text = message.text or str(message.content)
            result = await self._app.bot.send_message(
                chat_id=int(message.chat_id),
                text=text,
                parse_mode=self.config.options.get("parse_mode", "HTML"),
                reply_to_message_id=int(message.reply_to_id) if message.reply_to_id else None,
            )

            return Message(
                id=str(result.message_id),
                content=TextContent(text=text),
                chat_id=message.chat_id,
            )
        except Exception:
            logger.exception("telegram_send_failed")
            return None

    async def send_typing(self, chat_id: str) -> None:
        """Send typing indicator."""
        if self._app:
            try:
                await self._app.bot.send_chat_action(chat_id=int(chat_id), action="typing")
            except Exception:
                logger.exception("telegram_typing_failed")
