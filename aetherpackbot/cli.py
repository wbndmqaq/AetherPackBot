"""Command-line interface for AetherPackBot."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aetherpackbot.config.settings import Settings
    from aetherpackbot.core.engine import BotEngine


def main() -> int:
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        prog="aetherpack",
        description="AetherPackBot - Modern multi-platform chatbot framework",
    )

    parser.add_argument(
        "-c",
        "--config",
        type=str,
        default="config.yaml",
        help="Path to configuration file",
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Enable debug mode",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="API server host",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="API server port",
    )
    parser.add_argument(
        "--no-api",
        action="store_true",
        help="Disable API server",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="store_true",
        help="Show version and exit",
    )

    args = parser.parse_args()

    if args.version:
        from aetherpackbot import __version__

        print(f"AetherPackBot v{__version__}")
        return 0

    # Run the bot
    try:
        asyncio.run(run_bot(args))
    except KeyboardInterrupt:
        print("\nShutdown requested...")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


async def run_bot(args: argparse.Namespace) -> None:
    """Run the bot with given arguments."""
    from aetherpackbot.config.settings import Settings
    from aetherpackbot.core.engine import BotEngine
    from aetherpackbot.utils.logging import setup_logging

    # Load settings
    config_path = Path(args.config)
    if config_path.exists():
        settings = Settings.from_file(config_path)
    else:
        settings = Settings()

    # Override with CLI args
    if args.debug:
        settings.debug = True
        settings.logging.level = "DEBUG"

    # Setup logging
    setup_logging(
        level=settings.logging.level,
        format="console" if settings.debug else settings.logging.format,
    )

    # Create engine
    engine = BotEngine(settings=settings)

    # Setup platforms from config
    await setup_platforms(engine, settings)

    # Setup providers from config
    await setup_providers(engine, settings)

    # Start API server if enabled
    if not args.no_api and settings.api.enabled:
        from aetherpackbot.api.server import APIServer

        api_server = APIServer(
            engine,
            host=args.host or settings.api.host,
            port=args.port or settings.api.port,
        )
        await api_server.start()

    # Run engine
    await engine.run_forever()


async def setup_platforms(engine: BotEngine, settings: Settings) -> None:
    """Setup platforms from configuration."""
    # Telegram
    if settings.platforms.telegram.get("enabled") and settings.platforms.telegram.get("token"):
        from aetherpackbot.platforms.telegram import TelegramConfig, TelegramPlatform

        config = TelegramConfig(
            name="telegram",
            token=settings.platforms.telegram["token"],
        )
        engine.register_platform("telegram", TelegramPlatform(config))

    # Discord
    if settings.platforms.discord.get("enabled") and settings.platforms.discord.get("token"):
        from aetherpackbot.platforms.discord import DiscordConfig, DiscordPlatform

        config = DiscordConfig(
            name="discord",
            token=settings.platforms.discord["token"],
        )
        engine.register_platform("discord", DiscordPlatform(config))


async def setup_providers(engine: BotEngine, settings: Settings) -> None:
    """Setup LLM providers from configuration."""
    # OpenAI
    if settings.providers.openai.get("enabled") and settings.providers.openai.get("api_key"):
        from aetherpackbot.providers.openai import OpenAIConfig, OpenAIProvider

        config = OpenAIConfig(
            name="openai",
            api_key=settings.providers.openai["api_key"],
            model=settings.providers.openai.get("model", "gpt-4"),
        )
        engine.register_provider("openai", OpenAIProvider(config))

    # Anthropic
    if settings.providers.anthropic.get("enabled") and settings.providers.anthropic.get("api_key"):
        from aetherpackbot.providers.anthropic import AnthropicConfig, AnthropicProvider

        config = AnthropicConfig(
            name="anthropic",
            api_key=settings.providers.anthropic["api_key"],
            model=settings.providers.anthropic.get("model", "claude-3-opus-20240229"),
        )
        engine.register_provider("anthropic", AnthropicProvider(config))

    # Gemini
    if settings.providers.gemini.get("enabled") and settings.providers.gemini.get("api_key"):
        from aetherpackbot.providers.gemini import GeminiConfig, GeminiProvider

        config = GeminiConfig(
            name="gemini",
            api_key=settings.providers.gemini["api_key"],
            model=settings.providers.gemini.get("model", "gemini-pro"),
        )
        engine.register_provider("gemini", GeminiProvider(config))


if __name__ == "__main__":
    sys.exit(main())
