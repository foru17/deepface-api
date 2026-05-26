"""Health and readiness endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from ... import __version__

router = APIRouter()


@router.get("/health", summary="Liveness probe")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


@router.get("/ready", summary="Readiness probe")
async def ready() -> dict[str, str]:
    """Cheap readiness check. ML model warm-up happens on first request."""

    return {"status": "ready"}
