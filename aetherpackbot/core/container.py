"""Dependency injection container for service management."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar, get_type_hints

import structlog

logger = structlog.get_logger(__name__)

T = TypeVar("T")


class Container:
    """Simple dependency injection container."""

    def __init__(self) -> None:
        self._singletons: dict[type, Any] = {}
        self._factories: dict[type, Callable[..., Any]] = {}
        self._instances: dict[type, Any] = {}

    def register_singleton(self, interface: type[T], instance: T) -> None:
        """Register a singleton instance."""
        self._singletons[interface] = instance
        logger.debug("singleton_registered", type=interface.__name__)

    def register_factory(self, interface: type[T], factory: Callable[..., T]) -> None:
        """Register a factory function for creating instances."""
        self._factories[interface] = factory
        logger.debug("factory_registered", type=interface.__name__)

    def register_instance(self, interface: type[T], instance: T) -> None:
        """Register a specific instance (creates new each time if factory exists)."""
        self._instances[interface] = instance

    def resolve(self, interface: type[T]) -> T:
        """Resolve a dependency by type."""
        # Check singletons first
        if interface in self._singletons:
            return self._singletons[interface]

        # Check instances
        if interface in self._instances:
            return self._instances[interface]

        # Try factory
        if interface in self._factories:
            instance = self._factories[interface]()
            return instance

        raise KeyError(f"No registration found for {interface.__name__}")

    def resolve_optional(self, interface: type[T]) -> T | None:
        """Resolve a dependency, returning None if not found."""
        try:
            return self.resolve(interface)
        except KeyError:
            return None

    def has(self, interface: type) -> bool:
        """Check if a type is registered."""
        return (
            interface in self._singletons
            or interface in self._factories
            or interface in self._instances
        )

    def create_with_injection(self, cls: type[T]) -> T:
        """Create an instance with automatic dependency injection."""
        hints = get_type_hints(cls.__init__)
        hints.pop("return", None)

        kwargs: dict[str, Any] = {}
        for param_name, param_type in hints.items():
            if self.has(param_type):
                kwargs[param_name] = self.resolve(param_type)

        return cls(**kwargs)

    def clear(self) -> None:
        """Clear all registrations."""
        self._singletons.clear()
        self._factories.clear()
        self._instances.clear()


# Global container instance
_default_container: Container | None = None


def get_container() -> Container:
    """Get or create the global container."""
    global _default_container
    if _default_container is None:
        _default_container = Container()
    return _default_container
