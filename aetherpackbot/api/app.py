"""FastAPI application factory."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

if TYPE_CHECKING:
    from aetherpackbot.core.engine import BotEngine


def create_app(engine: BotEngine | None = None) -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="AetherPackBot API",
        description="RESTful API for AetherPackBot chatbot framework",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Store engine in app state
    app.state.engine = engine

    # Register routes
    from aetherpackbot.api.routes import chat, config, health, platforms, plugins, providers

    app.include_router(health.router, tags=["Health"])
    app.include_router(plugins.router, prefix="/api/plugins", tags=["Plugins"])
    app.include_router(platforms.router, prefix="/api/platforms", tags=["Platforms"])
    app.include_router(providers.router, prefix="/api/providers", tags=["Providers"])
    app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
    app.include_router(config.router, prefix="/api/config", tags=["Config"])

    # Static files for admin panel
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

        @app.get("/", include_in_schema=False)
        async def serve_admin_panel():
            """Serve the admin panel."""
            return FileResponse(static_dir / "index.html")

    return app
