"""Meta endpoints that are intentionally *not* tied to an API version.

Mounted at ``/api`` so the canonical path is ``/api/version``. A legacy
alias is also exposed at ``/version`` for clients that don't want to
hard-code the ``/api`` prefix.
"""

from __future__ import annotations

import os

from fastapi import APIRouter
from pydantic import BaseModel, Field

from .. import __version__
from .v1 import API_VERSION

router = APIRouter()


class VersionInfo(BaseModel):
    """Service version information."""

    package_version: str = Field(description="Python distribution version.")
    api_version: str = Field(description="Default / current HTTP API contract version.")
    api_versions: list[str] = Field(description="All HTTP API versions this build serves.")
    build_sha: str | None = Field(
        default=None,
        description="Git commit SHA the binary was built from (DEEPFACE_BUILD_SHA).",
    )
    build_time: str | None = Field(
        default=None,
        description="ISO-8601 build timestamp (DEEPFACE_BUILD_TIME).",
    )


@router.get(
    "/version",
    summary="Service version information",
    response_model=VersionInfo,
    tags=["meta"],
)
async def version() -> VersionInfo:
    return VersionInfo(
        package_version=__version__,
        api_version=API_VERSION,
        api_versions=[API_VERSION],
        build_sha=os.getenv("DEEPFACE_BUILD_SHA") or None,
        build_time=os.getenv("DEEPFACE_BUILD_TIME") or None,
    )
