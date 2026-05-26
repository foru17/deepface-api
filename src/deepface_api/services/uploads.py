"""Upload validation and decoding helpers."""

from __future__ import annotations

import cv2
import numpy as np
from fastapi import UploadFile

from ..exceptions import InvalidUploadError, UploadTooLargeError


async def read_and_decode_upload(
    file: UploadFile, max_upload_size_mb: int
) -> tuple[np.ndarray, bytes]:
    """Validate the uploaded file and decode it into a BGR numpy array.

    Raises:
        InvalidUploadError: content type is not an image, body is empty,
            or the bytes cannot be decoded as an image.
        UploadTooLargeError: payload exceeds the configured limit.
    """

    if not file.content_type or not file.content_type.startswith("image/"):
        raise InvalidUploadError("Only image uploads are supported (content-type image/*)")

    content = await file.read()
    if not content:
        raise InvalidUploadError("Empty upload")

    max_upload_size = max_upload_size_mb * 1024 * 1024
    if len(content) > max_upload_size:
        raise UploadTooLargeError(
            f"Upload too large. Maximum supported size is {max_upload_size_mb}MB"
        )

    nparr = np.frombuffer(content, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise InvalidUploadError("Could not decode image payload")

    return img, content
