"""Provider management routes."""

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter()


class ProviderInfo(BaseModel):
    """Provider information response."""

    name: str
    model: str | None = None
    enabled: bool = True


class ProviderListResponse(BaseModel):
    """List of providers response."""

    providers: list[ProviderInfo]
    total: int


@router.get("")
async def list_providers(request: Request) -> ProviderListResponse:
    """List all registered LLM providers."""
    engine = request.app.state.engine
    if not engine:
        return ProviderListResponse(providers=[], total=0)

    providers = []
    for name, provider in engine._providers.items():
        providers.append(
            ProviderInfo(
                name=name,
                model=getattr(provider, 'model', None),
                enabled=True,
            )
        )

    return ProviderListResponse(providers=providers, total=len(providers))


@router.get("/{name}")
async def get_provider(request: Request, name: str) -> ProviderInfo:
    """Get provider details."""
    engine = request.app.state.engine
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")

    provider = engine._providers.get(name)
    if not provider:
        raise HTTPException(status_code=404, detail=f"Provider '{name}' not found")

    return ProviderInfo(
        name=name,
        model=getattr(provider, 'model', None),
        enabled=True,
    )
