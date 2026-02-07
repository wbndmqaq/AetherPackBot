"""API module - RESTful web API with FastAPI."""

from aetherpackbot.api.app import create_app
from aetherpackbot.api.server import APIServer

__all__ = ["create_app", "APIServer"]
