"""Aggregated v1 router."""

from __future__ import annotations

from fastapi import APIRouter

from . import analyze, health

router = APIRouter()
router.include_router(health.router, tags=["health"])
router.include_router(analyze.router, tags=["analyze"])
