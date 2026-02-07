"""Plugin decorators for commands and event handlers."""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from aetherpackbot.core.events import Event, EventPriority

F = TypeVar("F", bound=Callable[..., Any])


def command(
    name: str | None = None,
    description: str = "",
    aliases: list[str] | None = None,
    usage: str = "",
) -> Callable[[F], F]:
    """Decorator to register a command handler."""

    def decorator(func: F) -> F:
        cmd_name = name or func.__name__

        # Store metadata on function
        func._command_info = {  # type: ignore
            "name": cmd_name,
            "description": description,
            "aliases": aliases or [],
            "usage": usage,
        }

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            return await func(*args, **kwargs)

        wrapper._command_info = func._command_info  # type: ignore
        return wrapper  # type: ignore

    return decorator


def handler(
    pattern: str | None = None,
    priority: int = 50,
) -> Callable[[F], F]:
    """Decorator to register a message handler."""

    def decorator(func: F) -> F:
        func._handler_info = {  # type: ignore
            "pattern": pattern,
            "priority": priority,
        }

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            return await func(*args, **kwargs)

        wrapper._handler_info = func._handler_info  # type: ignore
        return wrapper  # type: ignore

    return decorator


def on_event(
    event_type: type[Event],
    priority: EventPriority = EventPriority.NORMAL,
) -> Callable[[F], F]:
    """Decorator to register an event handler."""

    def decorator(func: F) -> F:
        func._event_info = {  # type: ignore
            "event_type": event_type,
            "priority": priority,
        }

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            return await func(*args, **kwargs)

        wrapper._event_info = func._event_info  # type: ignore
        return wrapper  # type: ignore

    return decorator


def requires_permission(*permissions: str) -> Callable[[F], F]:
    """Decorator to require specific permissions for a handler."""

    def decorator(func: F) -> F:
        func._required_permissions = list(permissions)  # type: ignore

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Permission check would happen here in actual use
            return await func(*args, **kwargs)

        wrapper._required_permissions = func._required_permissions  # type: ignore
        return wrapper  # type: ignore

    return decorator


def cooldown(seconds: float, per_user: bool = True) -> Callable[[F], F]:
    """Decorator to add cooldown to a command."""
    from collections import defaultdict
    from datetime import datetime, timezone

    last_used: dict[str, datetime] = defaultdict(lambda: datetime.min.replace(tzinfo=timezone.utc))

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(ctx: Any, *args: Any, **kwargs: Any) -> Any:
            key = ctx.user.id if per_user and ctx.user else "global"
            now = datetime.now(timezone.utc)
            elapsed = (now - last_used[key]).total_seconds()

            if elapsed < seconds:
                remaining = seconds - elapsed
                await ctx.reply(f"Please wait {remaining:.1f}s before using this again.")
                return None

            last_used[key] = now
            return await func(ctx, *args, **kwargs)

        return wrapper  # type: ignore

    return decorator
