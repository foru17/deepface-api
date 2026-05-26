"""Domain exceptions and FastAPI exception handlers."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .logging import logger


class APIError(Exception):
    """Base error type that maps to a structured JSON response."""

    status_code: int = 500
    code: str = "internal_error"

    def __init__(self, message: str, *, status_code: int | None = None, code: str | None = None):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        if code is not None:
            self.code = code


class InvalidUploadError(APIError):
    status_code = 400
    code = "invalid_upload"


class UploadTooLargeError(APIError):
    status_code = 413
    code = "upload_too_large"


def _error_payload(message: str, code: str, request_id: str | None = None) -> dict[str, str]:
    payload = {"status": "error", "code": code, "message": message}
    if request_id:
        payload["request_id"] = request_id
    return payload


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(APIError)
    async def _handle_api_error(request: Request, exc: APIError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_payload(
                exc.message, exc.code, getattr(request.state, "request_id", None)
            ),
        )

    # Register against the Starlette base so this also catches FastAPI's
    # HTTPException (subclass) *and* router-level 404 / 405 raised by
    # Starlette itself.
    @app.exception_handler(StarletteHTTPException)
    async def _handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        if exc.status_code == 404:
            code = "not_found"
        elif exc.status_code == 405:
            code = "method_not_allowed"
        elif exc.status_code < 500:
            code = "http_error"
        else:
            code = "internal_error"
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_payload(
                str(exc.detail), code, getattr(request.state, "request_id", None)
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def _handle_validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                **_error_payload(
                    "Request validation failed",
                    "validation_error",
                    getattr(request.state, "request_id", None),
                ),
                "details": exc.errors(),
            },
        )

    @app.exception_handler(Exception)
    async def _handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        logger.exception("unhandled error request_id=%s", request_id)
        return JSONResponse(
            status_code=500,
            content=_error_payload("Internal server error", "internal_error", request_id),
        )
