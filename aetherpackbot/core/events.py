"""Event system with priority-based dispatch."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import IntEnum
from typing import Any, TypeVar
from uuid import uuid4

import structlog

logger = structlog.get_logger(__name__)

T = TypeVar("T", bound="Event")
EventHandler = Callable[[T], Awaitable[None]]


class EventPriority(IntEnum):
    """Handler execution priority. Lower values execute first."""

    HIGHEST = 0
    HIGH = 25
    NORMAL = 50
    LOW = 75
    LOWEST = 100
    MONITOR = 1000  # For logging/analytics, always last


@dataclass
class Event:
    """Base event class. All events inherit from this."""

    id: str = field(default_factory=lambda: uuid4().hex[:12])
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    cancelled: bool = field(default=False)
    metadata: dict[str, Any] = field(default_factory=dict)

    def cancel(self) -> None:
        """Cancel event propagation."""
        self.cancelled = True


@dataclass
class HandlerInfo:
    """Information about a registered handler."""

    handler: EventHandler
    priority: EventPriority
    once: bool = False


class EventBus:
    """Async event bus with priority-based dispatch."""

    def __init__(self) -> None:
        self._handlers: dict[type[Event], list[HandlerInfo]] = defaultdict(list)
        self._lock = asyncio.Lock()

    def on(
        self,
        event_type: type[T],
        priority: EventPriority = EventPriority.NORMAL,
        once: bool = False,
    ) -> Callable[[EventHandler[T]], EventHandler[T]]:
        """Decorator to register an event handler."""

        def decorator(handler: EventHandler[T]) -> EventHandler[T]:
            self.subscribe(event_type, handler, priority, once)
            return handler

        return decorator

    def subscribe(
        self,
        event_type: type[T],
        handler: EventHandler[T],
        priority: EventPriority = EventPriority.NORMAL,
        once: bool = False,
    ) -> None:
        """Register a handler for an event type."""
        info = HandlerInfo(handler=handler, priority=priority, once=once)
        handlers = self._handlers[event_type]
        handlers.append(info)
        handlers.sort(key=lambda h: h.priority)
        logger.debug("handler_registered", event=event_type.__name__, priority=priority.name)

    def unsubscribe(self, event_type: type[T], handler: EventHandler[T]) -> bool:
        """Remove a handler. Returns True if found and removed."""
        handlers = self._handlers.get(event_type, [])
        for i, info in enumerate(handlers):
            if info.handler is handler:
                handlers.pop(i)
                logger.debug("handler_removed", event=event_type.__name__)
                return True
        return False

    async def emit(self, event: Event) -> Event:
        """Emit an event to all registered handlers."""
        event_type = type(event)
        handlers = list(self._handlers.get(event_type, []))

        to_remove: list[HandlerInfo] = []

        for info in handlers:
            if event.cancelled:
                logger.debug("event_cancelled", event_id=event.id)
                break

            try:
                await info.handler(event)
                if info.once:
                    to_remove.append(info)
            except Exception:
                logger.exception("handler_error", event=event_type.__name__)

        # Remove one-time handlers
        for info in to_remove:
            self._handlers[event_type].remove(info)

        return event

    async def emit_parallel(self, event: Event) -> Event:
        """Emit event to all handlers in parallel (ignores priority)."""
        event_type = type(event)
        handlers = self._handlers.get(event_type, [])

        tasks = [info.handler(event) for info in handlers]
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    logger.exception("parallel_handler_error", error=str(result))

        return event

    def clear(self, event_type: type[Event] | None = None) -> None:
        """Clear handlers for a specific event or all events."""
        if event_type:
            self._handlers[event_type].clear()
        else:
            self._handlers.clear()


# Global event bus instance
_default_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    """Get or create the global event bus."""
    global _default_bus
    if _default_bus is None:
        _default_bus = EventBus()
    return _default_bus
