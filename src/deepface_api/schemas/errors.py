"""Error response schema."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    status: str = "error"
    code: str
    message: str
    request_id: str | None = None
    details: Any | None = None
