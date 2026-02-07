"""Plugins module - extensible plugin system."""

from aetherpackbot.plugins.base import Plugin, PluginMeta
from aetherpackbot.plugins.decorators import command, handler, on_event
from aetherpackbot.plugins.loader import PluginLoader

__all__ = ["Plugin", "PluginMeta", "PluginLoader", "command", "handler", "on_event"]
