"""Plugin management routes."""

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter()


class PluginInfo(BaseModel):
    """Plugin information response."""

    name: str
    version: str
    description: str
    enabled: bool


class PluginListResponse(BaseModel):
    """List of plugins response."""

    plugins: list[PluginInfo]
    total: int


@router.get("")
async def list_plugins(request: Request) -> PluginListResponse:
    """List all loaded plugins."""
    engine = request.app.state.engine
    if not engine:
        return PluginListResponse(plugins=[], total=0)

    plugins = []
    for _, plugin in engine._plugins.items():
        plugins.append(
            PluginInfo(
                name=plugin.meta.name,
                version=plugin.meta.version,
                description=plugin.meta.description,
                enabled=plugin.meta.enabled,
            )
        )

    return PluginListResponse(plugins=plugins, total=len(plugins))


@router.get("/{name}")
async def get_plugin(request: Request, name: str) -> PluginInfo:
    """Get plugin details."""
    engine = request.app.state.engine
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")

    plugin = engine._plugins.get(name)
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Plugin '{name}' not found")

    return PluginInfo(
        name=plugin.meta.name,
        version=plugin.meta.version,
        description=plugin.meta.description,
        enabled=plugin.meta.enabled,
    )


@router.post("/{name}/reload")
async def reload_plugin(request: Request, name: str) -> dict[str, Any]:
    """Reload a plugin."""
    engine = request.app.state.engine
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")

    # This would reload the plugin
    return {"status": "reloaded", "name": name}
