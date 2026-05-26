"""Version 1 of the public HTTP API."""

from .router import router as v1_router

#: The numeric API contract version served under ``/api/v1``.
#: Bump when introducing a v2 router. Used by middleware to stamp the
#: ``X-API-Version`` response header and by the ``/api/version`` endpoint.
API_VERSION = "1"

__all__ = ["API_VERSION", "v1_router"]
