"""Unit tests for the upload validation service."""

from __future__ import annotations

import io

import pytest
from fastapi import UploadFile

from deepface_api.exceptions import InvalidUploadError, UploadTooLargeError
from deepface_api.services.uploads import read_and_decode_upload


def _make_upload(
    content: bytes, content_type: str = "image/jpeg", name: str = "x.jpg"
) -> UploadFile:
    return UploadFile(
        filename=name, file=io.BytesIO(content), headers={"content-type": content_type}
    )  # type: ignore[arg-type]


async def test_rejects_non_image_content_type() -> None:
    upload = _make_upload(b"hello", content_type="text/plain", name="x.txt")
    with pytest.raises(InvalidUploadError):
        await read_and_decode_upload(upload, max_upload_size_mb=1)


async def test_rejects_empty_body(sample_image_bytes: bytes) -> None:
    upload = _make_upload(b"", content_type="image/jpeg")
    with pytest.raises(InvalidUploadError):
        await read_and_decode_upload(upload, max_upload_size_mb=1)


async def test_rejects_oversized(sample_image_bytes: bytes) -> None:
    payload = b"\x00" * (2 * 1024 * 1024)
    upload = _make_upload(payload, content_type="image/jpeg")
    with pytest.raises(UploadTooLargeError):
        await read_and_decode_upload(upload, max_upload_size_mb=1)


async def test_rejects_undecodable(sample_image_bytes: bytes) -> None:
    upload = _make_upload(b"not really a jpeg", content_type="image/jpeg")
    with pytest.raises(InvalidUploadError):
        await read_and_decode_upload(upload, max_upload_size_mb=1)


async def test_decodes_valid_jpeg(sample_image_bytes: bytes) -> None:
    upload = _make_upload(sample_image_bytes, content_type="image/jpeg")
    img, raw = await read_and_decode_upload(upload, max_upload_size_mb=1)
    assert img is not None
    assert img.shape[2] == 3
    assert len(raw) == len(sample_image_bytes)
