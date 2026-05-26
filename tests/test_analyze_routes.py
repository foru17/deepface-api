"""End-to-end tests for the analyze routes with mocked inference."""

from __future__ import annotations


def test_analyze_rejects_non_image_upload(client) -> None:
    response = client.post(
        "/analyze",
        files={"file": ("not-image.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 400
    body = response.json()
    assert body["status"] == "error"
    assert body["code"] == "invalid_upload"
    assert "image" in body["message"].lower()


def test_analyze_rejects_oversized_upload(client) -> None:
    big = b"\x00" * (2 * 1024 * 1024)  # 2 MB > 1 MB test limit
    response = client.post(
        "/analyze",
        files={"file": ("big.jpg", big, "image/jpeg")},
    )
    assert response.status_code == 413
    assert response.json()["code"] == "upload_too_large"


def test_analyze_returns_face_metadata(client, mock_vision, upload_payload) -> None:
    response = client.post("/analyze", files=upload_payload())
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["faces_detected"] == 1
    face = body["faces"][0]
    assert face["age"] == 30
    assert face["gender"] == "Woman"
    assert face["dominant_emotion"] == "happy"
    assert face["dominant_race"] == "asian"
    assert face["output_file"] is None if "output_file" in face else True


def test_analyze_save_render_writes_file(
    client, mock_vision, upload_payload, settings, tmp_path
) -> None:
    response = client.post(
        "/analyze",
        params={"save_render": "true"},
        files=upload_payload(),
    )
    assert response.status_code == 200, response.text
    output_file = response.json().get("output_file")
    assert output_file
    assert (tmp_path / "output").exists()


def test_detect_and_return_responds_with_jpeg(client, mock_vision, upload_payload) -> None:
    response = client.post("/detect_and_return", files=upload_payload())
    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("image/jpeg")
    assert response.headers["X-Faces-Detected"] == "1"
    assert response.headers["X-Detection-Status"] == "success"
    assert len(response.content) > 0


def test_detect_and_return_lightweight_overlay(client, mock_vision, upload_payload) -> None:
    response = client.post(
        "/detect_and_return",
        params={"info_display": "true"},
        files=upload_payload(),
    )
    assert response.status_code == 200
    assert response.headers["X-Detection-Status"] == "success"


def test_openapi_schema_is_served(client) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/v1/analyze" in paths
    assert "/api/v1/health" in paths
