"""Shared pytest fixtures.

The heavy ML dependencies (TensorFlow, RetinaFace, DeepFace) take many
seconds to import and need GPU/CPU model downloads at runtime. For unit
tests we patch the inference helpers, which lets the full test suite run
in CI in under a few seconds on a tiny runner.
"""

from __future__ import annotations

import io
from collections.abc import Iterator
from pathlib import Path

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from deepface_api.config import Settings, get_settings
from deepface_api.main import create_app


@pytest.fixture(scope="session")
def sample_image_bytes() -> bytes:
    """A small synthetic JPEG (no real faces) usable as upload payload."""

    img = np.full((128, 128, 3), 200, dtype=np.uint8)
    cv2.rectangle(img, (32, 32), (96, 96), (0, 0, 0), 2)
    ok, encoded = cv2.imencode(".jpg", img)
    assert ok, "cv2 failed to encode test image"
    return encoded.tobytes()


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        output_dir=tmp_path / "output",
        max_upload_size_mb=1,
        cors_origins=["*"],
        enable_docs=True,
        log_level="WARNING",
    )


@pytest.fixture
def app(settings: Settings):
    application = create_app(settings=settings)
    application.dependency_overrides[get_settings] = lambda: settings
    return application


@pytest.fixture
def client(app) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def fake_detected_face() -> dict:
    return {
        "position": {"x": 10, "y": 20, "w": 50, "h": 60},
        "confidence": 0.987,
    }


@pytest.fixture
def fake_analysis() -> dict:
    return {
        "age": 30,
        "gender": "Woman",
        "dominant_emotion": "happy",
        "emotion": {"happy": 99.0, "sad": 1.0},
        "dominant_race": "asian",
        "race": {"asian": 90.0, "white": 10.0},
    }


@pytest.fixture
def mock_vision(monkeypatch, fake_detected_face, fake_analysis):
    """Patch the inference helpers used by the analyze router."""

    async def _fake_detect(_img):
        return [fake_detected_face]

    async def _fake_analyze(_img, _area, include_race: bool, lightweight: bool = False):
        result = {
            "age": fake_analysis["age"],
            "gender": fake_analysis["gender"],
            "dominant_emotion": fake_analysis["dominant_emotion"],
        }
        if not lightweight:
            result["emotion"] = fake_analysis["emotion"]
        if include_race and not lightweight:
            result["dominant_race"] = fake_analysis["dominant_race"]
            result["race"] = fake_analysis["race"]
        return result

    import deepface_api.api.v1.analyze as analyze_module

    monkeypatch.setattr(analyze_module, "detect_faces", _fake_detect)
    monkeypatch.setattr(analyze_module, "analyze_single_face", _fake_analyze)

    return


@pytest.fixture
def upload_payload(sample_image_bytes: bytes):
    def _build(name: str = "sample.jpg", content_type: str = "image/jpeg") -> dict:
        return {"file": (name, io.BytesIO(sample_image_bytes), content_type)}

    return _build
