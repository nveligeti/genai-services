# app/modules/health/router.py
# Chapter 2: Modular router pattern
# Chapter 4: Typed response with Pydantic BaseModel

from fastapi import APIRouter
from pydantic import BaseModel
from app.settings import get_settings

router = APIRouter(prefix="/health", tags=["Health"])


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str


@router.get("", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    Never rate-limited (Chapter 9).
    Used by Docker health checks (Chapter 12).
    """
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        environment=settings.environment,
    )
