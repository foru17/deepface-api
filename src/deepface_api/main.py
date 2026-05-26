"""Application factory and ASGI entrypoint."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import __version__
from .api.meta import router as meta_router
from .api.v1 import API_VERSION, v1_router
from .config import Settings, get_settings
from .exceptions import register_exception_handlers
from .logging import configure_logging, logger
from .middleware import APIVersionHeaderMiddleware, RequestIDMiddleware

# Legacy unversioned routes that should still advertise the default API
# version via the ``X-API-Version`` header. Keep in sync with v1 routes.
_LEGACY_PATHS = {
    "/analyze",
    "/detect_and_return",
    "/health",
    "/ready",
    "/version",
}


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    logger.info(
        "starting deepface-api version=%s port=%s output_dir=%s",
        __version__,
        settings.server_port,
        settings.output_dir,
    )
    yield
    logger.info("shutting down deepface-api")


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build a FastAPI application instance.

    Exposed as a factory so tests can override settings via dependency
    injection and so deployment platforms can call
    ``deepface_api.main:create_app`` with ``--factory``.
    """

    settings = settings or get_settings()
    configure_logging(level=settings.log_level, as_json=settings.log_json)

    app = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        version=__version__,
        docs_url="/docs" if settings.enable_docs else None,
        redoc_url="/redoc" if settings.enable_docs else None,
        openapi_url="/openapi.json" if settings.enable_docs else None,
        lifespan=_lifespan,
    )
    app.state.settings = settings

    # Make Settings available via DI in routes, overridable in tests.
    app.dependency_overrides.setdefault(get_settings, lambda: settings)

    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(
        APIVersionHeaderMiddleware,
        default_version=API_VERSION,
        legacy_paths=_LEGACY_PATHS,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=[
            "X-Request-ID",
            "X-API-Version",
            "X-Faces-Detected",
            "X-Detection-Status",
        ],
    )

    register_exception_handlers(app)

    # Versioned API (canonical, documented in OpenAPI).
    app.include_router(v1_router, prefix="/api/v1")
    # Backwards-compatible unversioned aliases (hidden from OpenAPI to keep
    # the schema clean — they share handlers with the v1 router).
    app.include_router(v1_router, include_in_schema=False)

    # Meta endpoints — not tied to an API version.
    app.include_router(meta_router, prefix="/api", tags=["meta"])
    app.include_router(meta_router, include_in_schema=False)

    return app


app = create_app()
