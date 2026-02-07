"""Core bot engine - orchestrates all components."""

from __future__ import annotations

import asyncio
import signal
from typing import TYPE_CHECKING

import structlog

from aetherpackbot.core.container import Container, get_container
from aetherpackbot.core.events import Event, EventBus, get_event_bus

if TYPE_CHECKING:
    from aetherpackbot.config.settings import Settings
    from aetherpackbot.platforms.base import Platform
    from aetherpackbot.plugins.base import Plugin
    from aetherpackbot.providers.base import LLMProvider

logger = structlog.get_logger(__name__)


class EngineStartedEvent(Event):
    """Fired when engine completes startup."""

    pass


class EngineStoppingEvent(Event):
    """Fired when engine begins shutdown."""

    pass


class BotEngine:
    """Main bot engine that coordinates all subsystems."""

    def __init__(
        self,
        settings: Settings | None = None,
        container: Container | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        self.container = container or get_container()
        self.event_bus = event_bus or get_event_bus()
        self._settings = settings
        self._platforms: dict[str, Platform] = {}
        self._providers: dict[str, LLMProvider] = {}
        self._plugins: dict[str, Plugin] = {}
        self._running = False
        self._shutdown_event = asyncio.Event()

        # Register self in container
        self.container.register_singleton(BotEngine, self)
        self.container.register_singleton(EventBus, self.event_bus)

    @property
    def settings(self) -> Settings:
        """Get settings, loading if needed."""
        if self._settings is None:
            from aetherpackbot.config.settings import Settings

            self._settings = Settings()
        return self._settings

    def register_platform(self, name: str, platform: Platform) -> None:
        """Register a messaging platform adapter."""
        self._platforms[name] = platform
        platform.engine = self
        logger.info("platform_registered", name=name)

    def register_provider(self, name: str, provider: LLMProvider) -> None:
        """Register an LLM provider."""
        self._providers[name] = provider
        logger.info("provider_registered", name=name)

    def register_plugin(self, name: str, plugin: Plugin) -> None:
        """Register a plugin."""
        self._plugins[name] = plugin
        plugin.engine = self
        logger.info("plugin_registered", name=name)

    def get_platform(self, name: str) -> Platform | None:
        """Get a registered platform by name."""
        return self._platforms.get(name)

    def get_provider(self, name: str) -> LLMProvider | None:
        """Get a registered provider by name."""
        return self._providers.get(name)

    def get_default_provider(self) -> LLMProvider | None:
        """Get the default LLM provider."""
        if not self._providers:
            return None
        default_name = self.settings.default_provider
        if default_name and default_name in self._providers:
            return self._providers[default_name]
        return next(iter(self._providers.values()))

    async def start(self) -> None:
        """Start the bot engine and all components."""
        if self._running:
            logger.warning("engine_already_running")
            return

        logger.info("engine_starting", version="1.0.0")
        self._running = True

        # Initialize plugins
        for name, plugin in self._plugins.items():
            try:
                await plugin.on_load()
                logger.info("plugin_loaded", name=name)
            except Exception:
                logger.exception("plugin_load_failed", name=name)

        # Start platforms
        platform_tasks = []
        for name, platform in self._platforms.items():
            try:
                task = asyncio.create_task(platform.start())
                platform_tasks.append(task)
                logger.info("platform_started", name=name)
            except Exception:
                logger.exception("platform_start_failed", name=name)

        await self.event_bus.emit(EngineStartedEvent())
        logger.info("engine_started")

        # Wait for shutdown signal
        await self._shutdown_event.wait()

    async def stop(self) -> None:
        """Gracefully stop the engine."""
        if not self._running:
            return

        logger.info("engine_stopping")
        await self.event_bus.emit(EngineStoppingEvent())

        # Stop platforms
        for name, platform in self._platforms.items():
            try:
                await platform.stop()
                logger.info("platform_stopped", name=name)
            except Exception:
                logger.exception("platform_stop_failed", name=name)

        # Unload plugins
        for name, plugin in self._plugins.items():
            try:
                await plugin.on_unload()
                logger.info("plugin_unloaded", name=name)
            except Exception:
                logger.exception("plugin_unload_failed", name=name)

        self._running = False
        self._shutdown_event.set()
        logger.info("engine_stopped")

    def request_shutdown(self) -> None:
        """Request engine shutdown."""
        self._shutdown_event.set()

    async def run_forever(self) -> None:
        """Run the engine with signal handling."""
        loop = asyncio.get_event_loop()

        def signal_handler() -> None:
            logger.info("shutdown_signal_received")
            asyncio.create_task(self.stop())

        try:
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(sig, signal_handler)
        except NotImplementedError:
            # Windows doesn't support signal handlers in event loop
            pass

        await self.start()

    @property
    def is_running(self) -> bool:
        """Check if engine is running."""
        return self._running
