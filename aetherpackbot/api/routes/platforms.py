"""Platform management routes."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter()


class PlatformInfo(BaseModel):
    """Platform information response."""

    name: str
    connected: bool
    type: str


class PlatformListResponse(BaseModel):
    """List of platforms response."""

    platforms: list[PlatformInfo]
    total: int


@router.get("")
async def list_platforms(request: Request) -> PlatformListResponse:
    """List all registered platforms."""
    engine = request.app.state.engine
    if not engine:
        return PlatformListResponse(platforms=[], total=0)

    platforms = []
    for name, platform in engine._platforms.items():
        platforms.append(
            PlatformInfo(
                name=name,
                connected=platform.is_connected,
                type=platform.name,
            )
        )

    return PlatformListResponse(platforms=platforms, total=len(platforms))


@router.get("/{name}")
async def get_platform(request: Request, name: str) -> PlatformInfo:
    """Get platform details."""
    engine = request.app.state.engine
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")

    platform = engine.get_platform(name)
    if not platform:
        raise HTTPException(status_code=404, detail=f"Platform '{name}' not found")

    return PlatformInfo(
        name=name,
        connected=platform.is_connected,
        type=platform.name,
    )


@router.post("/{name}/reconnect")
async def reconnect_platform(request: Request, name: str) -> dict[str, str]:
    """Reconnect a platform."""
    engine = request.app.state.engine
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")

    platform = engine.get_platform(name)
    if not platform:
        raise HTTPException(status_code=404, detail=f"Platform '{name}' not found")

    try:
        await platform.stop()
        await platform.start()
        return {"status": "reconnected", "name": name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
