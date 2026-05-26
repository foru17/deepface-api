# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `API_VERSION` constant in `deepface_api.api.v1` as the single source
  of truth for the HTTP API contract version.
- `APIVersionHeaderMiddleware` stamps every API response with
  `X-API-Version` (extracted from `/api/vN/` paths or the configured
  default for legacy aliases).
- `GET /api/version` (alias `GET /version`) returns
  `{ package_version, api_version, api_versions, build_sha, build_time }`.
  `build_sha` and `build_time` are populated from `DEEPFACE_BUILD_SHA`
  and `DEEPFACE_BUILD_TIME` env vars set at image-build time.
- `docs/VERSIONING.md` documents SemVer scope, breaking-change
  guidelines, deprecation window, and image-tag policy.

## [2.0.0] - 2026-05-23

### Added
- PEP 621 packaging via `pyproject.toml` with `dev`, `test`, `docs`, `gpu`
  optional dependency groups; project is now installable as the
  `deepface-api` distribution and ships a `deepface-api` console script.
- Versioned HTTP API under `/api/v1/*` (`/api/v1/analyze`,
  `/api/v1/detect_and_return`, `/api/v1/health`, `/api/v1/ready`).
- `pydantic-settings` configuration with the `DEEPFACE_` env prefix and
  CORS / log-level / log-json / docs-enable knobs.
- `RequestIDMiddleware` (echoes / generates `X-Request-ID`) and
  consistent JSON error responses with `code`, `message`, and `request_id`.
- Multi-stage `Dockerfile` (slim runtime, non-root user, HEALTHCHECK,
  BuildKit cache mounts) and optional CUDA-enabled `Dockerfile.gpu`.
- GHCR publishing workflow with multi-arch (linux/amd64 + linux/arm64)
  builds, SBOM, and SLSA provenance attestation.
- CodeQL security analysis, Dependabot for pip / actions / docker,
  expanded pre-commit (ruff-format, hadolint, large-file guard).
- Test suite (26 tests, ~83% coverage) that mocks heavy ML dependencies
  so CI completes in seconds.
- `docs/ARCHITECTURE.md` and `docs/DEPLOYMENT.md`, plus CHANGELOG and
  refreshed README with badges, client examples, and config matrix.

### Changed
- Source layout moved from `app/` to `src/deepface_api/` (PyPA standard).
- Default OpenCV dependency switched to `opencv-python-headless` for
  smaller containers and no GUI library requirement.
- TensorFlow pin loosened to `>=2.13,<2.18` and platform-aware
  (`tensorflow-macos` on Apple Silicon).
- Python version support: now 3.10, 3.11, 3.12.
- Docker image runtime path changed: data volume mounts at `/data/output`.

### Removed
- `requirements.txt` is no longer the canonical dep manifest (kept as a
  convenience file generated from `pyproject.toml`).
- Top-level `api.py` entry shim (use `deepface-api`, `python -m
  deepface_api`, or `uvicorn deepface_api.main:app`).

## [1.2.0] - 2026-02-19

Initial public release. Basic FastAPI service with `/analyze`,
`/detect_and_return`, and `/health` endpoints.
