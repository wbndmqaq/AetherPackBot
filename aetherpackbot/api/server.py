"""API server for running FastAPI with uvicorn."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from aetherpackbot.core.engine import BotEngine

logger = structlog.get_logger(__name__)


class APIServer:
    """Manages the FastAPI server lifecycle."""

    def __init__(
        self,
        engine: BotEngine,
        host: str = "0.0.0.0",
        port: int = 8080,
    ) -> None:
        self.engine = engine
        self.host = host
        self.port = port
        self._server = None
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start the API server."""
        try:
            import uvicorn

            from aetherpackbot.api.app import create_app

            app = create_app(self.engine)

            config = uvicorn.Config(
                app,
                host=self.host,
                port=self.port,
                log_level="info",
                access_log=False,
            )
            self._server = uvicorn.Server(config)

            self._task = asyncio.create_task(self._server.serve())
            logger.info("api_server_started", host=self.host, port=self.port)

        except ImportError:
            logger.error("uvicorn_not_installed", hint="pip install uvicorn")
            raise

    async def stop(self) -> None:
        """Stop the API server."""
        if self._server:
            self._server.should_exit = True
            if self._task:
                await self._task
            logger.info("api_server_stopped")

    @property
    def url(self) -> str:
        """Get the server URL."""
        return f"http://{self.host}:{self.port}"
