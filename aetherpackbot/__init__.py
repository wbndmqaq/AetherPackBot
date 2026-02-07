"""AetherPackBot - A modern multi-platform chatbot framework."""

__version__ = "1.0.0"
__author__ = "AetherPackBot Team"

from aetherpackbot.core.context import Context
from aetherpackbot.core.engine import BotEngine
from aetherpackbot.core.events import Event, EventBus

__all__ = ["BotEngine", "Context", "Event", "EventBus", "__version__"]
