"""Health check routes."""

from fastapi import APIRouter, Response
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str


@router.get("/health")
async def health_check() -> HealthResponse:
    """Check API health status."""
    return HealthResponse(status="healthy", version="1.0.0")


@router.get("/ready")
async def readiness_check() -> dict[str, bool]:
    """Check if service is ready to accept requests."""
    return {"ready": True}


@router.get("/live")
async def liveness_check(response: Response) -> dict[str, bool]:
    """Check if service is alive."""
    return {"alive": True}
