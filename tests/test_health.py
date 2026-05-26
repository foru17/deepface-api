"""Health and readiness endpoints."""

from __future__ import annotations


def test_health_returns_ok(client) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_health_also_available_under_v1(client) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ready_endpoint(client) -> None:
    response = client.get("/api/v1/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_request_id_header_is_set(client) -> None:
    response = client.get("/health")
    assert response.headers.get("x-request-id")


def test_request_id_is_echoed(client) -> None:
    response = client.get("/health", headers={"x-request-id": "abc-123"})
    assert response.headers.get("x-request-id") == "abc-123"
