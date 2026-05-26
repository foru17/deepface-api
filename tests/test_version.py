"""Tests for the version metadata endpoint and X-API-Version header."""

from __future__ import annotations


def test_version_endpoint_returns_metadata(client) -> None:
    response = client.get("/api/version")
    assert response.status_code == 200
    body = response.json()
    assert body["package_version"]
    assert body["api_version"] == "1"
    assert "1" in body["api_versions"]
    assert "build_sha" in body
    assert "build_time" in body


def test_version_endpoint_legacy_alias(client) -> None:
    response = client.get("/version")
    assert response.status_code == 200
    assert response.json()["api_version"] == "1"


def test_version_endpoint_picks_up_build_env(client, monkeypatch) -> None:
    monkeypatch.setenv("DEEPFACE_BUILD_SHA", "abc1234")
    monkeypatch.setenv("DEEPFACE_BUILD_TIME", "2026-05-26T12:00:00Z")
    response = client.get("/api/version")
    body = response.json()
    assert body["build_sha"] == "abc1234"
    assert body["build_time"] == "2026-05-26T12:00:00Z"


def test_x_api_version_header_on_v1_route(client) -> None:
    response = client.get("/api/v1/health")
    assert response.headers.get("x-api-version") == "1"


def test_x_api_version_header_on_legacy_route(client) -> None:
    response = client.get("/health")
    assert response.headers.get("x-api-version") == "1"


def test_x_api_version_header_on_meta_route(client) -> None:
    response = client.get("/api/version")
    assert response.headers.get("x-api-version") == "1"


def test_x_api_version_header_absent_on_docs(client) -> None:
    response = client.get("/openapi.json")
    assert "x-api-version" not in response.headers


def test_version_endpoint_listed_in_openapi(client) -> None:
    response = client.get("/openapi.json")
    paths = response.json()["paths"]
    assert "/api/version" in paths
