"""ASGI middlewares used by the application."""

from __future__ import annotations

import re
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from .logging import logger


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach an X-Request-ID header (generate if missing) and log latency."""

    HEADER = "x-request-id"

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        request_id = request.headers.get(self.HEADER) or uuid.uuid4().hex
        request.state.request_id = request_id

        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.exception(
                "request failed method=%s path=%s elapsed_ms=%.1f request_id=%s",
                request.method,
                request.url.path,
                elapsed_ms,
                request_id,
            )
            raise

        elapsed_ms = (time.perf_counter() - start) * 1000
        response.headers[self.HEADER] = request_id
        logger.info(
            "request method=%s path=%s status=%s elapsed_ms=%.1f request_id=%s",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
            request_id,
        )
        return response


class APIVersionHeaderMiddleware(BaseHTTPMiddleware):
    """Stamp ``X-API-Version`` on responses to API routes.

    Resolution rules:

    * ``/api/vN/...`` paths advertise ``N`` (extracted from the URL).
    * Legacy unversioned aliases (``/analyze``, ``/health`` etc.) and the
      meta endpoints under ``/api/`` advertise the configured default.
    * Documentation / OpenAPI routes get no header.
    """

    HEADER = "x-api-version"
    _VERSIONED = re.compile(r"^/api/v(\d+)(/|$)")
    _SKIP_PREFIXES = ("/docs", "/redoc", "/openapi.json", "/static")

    def __init__(self, app: ASGIApp, default_version: str, legacy_paths: set[str]) -> None:
        super().__init__(app)
        self.default_version = default_version
        self.legacy_paths = legacy_paths

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        response = await call_next(request)
        path = request.url.path

        if any(path.startswith(prefix) for prefix in self._SKIP_PREFIXES):
            return response

        match = self._VERSIONED.match(path)
        if match:
            response.headers[self.HEADER] = match.group(1)
        elif path.startswith("/api/") or path in self.legacy_paths:
            response.headers[self.HEADER] = self.default_version

        return response
