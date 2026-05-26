"""Unit tests for the pure-Python parts of the vision service.

These don't import RetinaFace or DeepFace.
"""

from __future__ import annotations

import numpy as np

from deepface_api.services.vision import (
    draw_detections_with_info,
    ensure_face_area_within_bounds,
)


def test_ensure_face_area_clips_to_image() -> None:
    area = {"x": -10, "y": -10, "w": 1000, "h": 1000}
    clipped = ensure_face_area_within_bounds(area, (100, 200, 3))
    assert clipped["x"] >= 0
    assert clipped["y"] >= 0
    assert clipped["x"] + clipped["w"] <= 200
    assert clipped["y"] + clipped["h"] <= 100


def test_ensure_face_area_keeps_valid_box() -> None:
    area = {"x": 5, "y": 10, "w": 50, "h": 30}
    clipped = ensure_face_area_within_bounds(area, (200, 200, 3))
    assert clipped == area


def test_draw_detections_does_not_mutate_input() -> None:
    img = np.full((100, 100, 3), 128, dtype=np.uint8)
    original = img.copy()
    out = draw_detections_with_info(
        img,
        [{"facial_area": {"x": 10, "y": 10, "w": 30, "h": 30}, "score": 0.9, "age": 25}],
    )
    np.testing.assert_array_equal(img, original)
    assert out.shape == img.shape
    assert not np.array_equal(out, img)


def test_draw_detections_handles_empty_list() -> None:
    img = np.full((50, 50, 3), 0, dtype=np.uint8)
    out = draw_detections_with_info(img, [])
    np.testing.assert_array_equal(out, img)
