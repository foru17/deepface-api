"""deepface-api — Face detection and facial attribute analysis HTTP API."""

from __future__ import annotations

from importlib import metadata as _metadata

__all__ = ["__version__"]

try:
    __version__ = _metadata.version("deepface-api")
except _metadata.PackageNotFoundError:  # source checkout, not installed
    from ._version import __version__  # type: ignore[no-redef]
