"""Schema validation tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from deepface_api.schemas import AnalyzeResponse, FaceAnalysis, FacePosition
from deepface_api.schemas.errors import ErrorResponse


def test_face_position_validates_non_negative_coords() -> None:
    with pytest.raises(ValidationError):
        FacePosition(x=-1, y=0, w=1, h=1)


def test_face_position_requires_positive_dimensions() -> None:
    with pytest.raises(ValidationError):
        FacePosition(x=0, y=0, w=0, h=10)


def test_face_analysis_is_lenient_to_missing_fields() -> None:
    face = FaceAnalysis(position=FacePosition(x=0, y=0, w=1, h=1))
    assert face.age is None
    assert face.confidence is None


def test_analyze_response_round_trip() -> None:
    payload = {
        "status": "success",
        "faces_detected": 1,
        "faces": [
            {
                "position": {"x": 1, "y": 2, "w": 3, "h": 4},
                "confidence": 0.5,
                "age": 22,
                "gender": "Woman",
            }
        ],
    }
    resp = AnalyzeResponse.model_validate(payload)
    assert resp.faces_detected == 1
    assert resp.faces[0].gender == "Woman"


def test_error_response_shape() -> None:
    err = ErrorResponse(code="x", message="m")
    dumped = err.model_dump()
    assert dumped["status"] == "error"
    assert dumped["code"] == "x"
