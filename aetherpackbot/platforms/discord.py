"""Discord platform adapter."""

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
class DiscordConfig(PlatformConfig):
    """Discord-specific configuration."""

    token: str = ""
    command_prefix: str = "!"
    intents: list[str] | None = None


class DiscordMessageEvent(Event):
    """Event fired when a Discord message is received."""

    context: Context | None = None


class DiscordPlatform(Platform):
    """Discord.py adapter."""

    name = "discord"

    def __init__(self, config: DiscordConfig) -> None:
        super().__init__(config)
        self._client = None
        self._token = config.token

    async def start(self) -> None:
        """Start the Discord bot."""
        try:
            import discord

            intents = discord.Intents.default()
            intents.message_content = True
            intents.members = True

            self._client = discord.Client(intents=intents)

            @self._client.event
            async def on_ready() -> None:
                self._connected = True
                logger.info("discord_ready", user=str(self._client.user))

            @self._client.event
            async def on_message(message: discord.Message) -> None:
                if message.author == self._client.user:
                    return
                await self._handle_message(message)

            # Start client in background
            import asyncio

            asyncio.create_task(self._client.start(self._token))
            logger.info("discord_starting")

        except ImportError:
            logger.error("discord_not_installed", hint="pip install discord.py")
            raise
        except Exception:
            logger.exception("discord_start_failed")
            raise

    async def stop(self) -> None:
        """Stop the Discord bot."""
        if self._client:
            await self._client.close()
        self._connected = False
        logger.info("discord_stopped")

    async def _handle_message(self, msg: Any) -> None:
        """Handle incoming Discord message."""
        ctx = self._build_context(msg)

        if self.engine:
            event = DiscordMessageEvent()
            event.context = ctx
            await self.engine.event_bus.emit(event)
            await self.on_message(ctx)

    def _build_context(self, msg: Any) -> Context:
        """Build context from Discord message."""
        user = User(
            id=str(msg.author.id),
            platform_id=f"discord:{msg.author.id}",
            username=msg.author.name,
            display_name=msg.author.display_name,
            is_bot=msg.author.bot,
        )

        chat_type = "private" if msg.guild is None else "group"
        chat = Chat(
            id=str(msg.channel.id),
            platform_id=f"discord:{msg.channel.id}",
            type=chat_type,
            title=getattr(msg.channel, "name", "DM"),
        )

        message = Message(
            id=str(msg.id),
            content=TextContent(text=msg.content),
            chat_id=str(msg.channel.id),
            sender_id=str(msg.author.id),
            platform_data={"discord_message": msg},
        )

        return Context(
            message=message,
            user=user,
            chat=chat,
            platform=self,
        )

    async def send_message(self, message: Message) -> Message | None:
        """Send a message to Discord."""
        if not self._client or not message.chat_id:
            return None

        try:
            channel = self._client.get_channel(int(message.chat_id))
            if not channel:
                channel = await self._client.fetch_channel(int(message.chat_id))

            text = message.text or str(message.content)
            result = await channel.send(text)

            return Message(
                id=str(result.id),
                content=TextContent(text=text),
                chat_id=message.chat_id,
            )
        except Exception:
            logger.exception("discord_send_failed")
            return None

    async def send_typing(self, chat_id: str) -> None:
        """Send typing indicator."""
        if self._client:
            try:
                channel = self._client.get_channel(int(chat_id))
                if channel:
                    await channel.typing()
            except Exception:
                logger.exception("discord_typing_failed")
