"""``python -m deepface_api`` — start the HTTP server with uvicorn."""

from __future__ import annotations


def main() -> None:
    import uvicorn

    from .config import get_settings

    settings = get_settings()
    uvicorn.run(
        "deepface_api.main:app",
        host=settings.server_host,
        port=settings.server_port,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
