# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.0.0] - 2026-05-27

A full rewrite of the project as a production-ready open-source FastAPI
service. The previous flat `app/` + `api.py` layout is gone; the
canonical entry points are now `deepface-api` (console script),
`python -m deepface_api`, and `uvicorn deepface_api.main:app`.

### Added

- **PEP 621 packaging** in `pyproject.toml` with `dev`, `test`, `docs`,
  `gpu` optional dependency groups; project installs as the
  `deepface-api` distribution.
- **Versioned HTTP API** under `/api/v1/*` (`analyze`,
  `detect_and_return`, `health`, `ready`) with unversioned legacy
  aliases hidden from the OpenAPI schema.
- **`API_VERSION` constant** in `deepface_api.api.v1` as the single
  source of truth for the HTTP API contract version.
- **`APIVersionHeaderMiddleware`** stamps `X-API-Version` on every
  API response (extracted from `/api/vN/` paths or the configured
  default for legacy aliases).
- **`GET /api/version`** (alias `GET /version`) returns
  `{ package_version, api_version, api_versions, build_sha, build_time }`.
  `build_sha` / `build_time` are injected at image-build time via
  `DEEPFACE_BUILD_SHA` / `DEEPFACE_BUILD_TIME` env vars.
- **`pydantic-settings`** configuration with the `DEEPFACE_` env prefix,
  CORS / log-level / log-json / docs-enable knobs, and `.env` support.
- **`RequestIDMiddleware`** echoes or generates `X-Request-ID` and logs
  method / path / status / latency / request_id per request.
- **Consistent JSON error envelope** (`status`, `code`, `message`,
  `request_id`) for `APIError` subclasses, `HTTPException`, validation
  failures, 404 / 405, and unhandled exceptions.
- **Multi-stage `Dockerfile`** (slim runtime, non-root user uid 10001,
  curl-based `HEALTHCHECK`, BuildKit cache mounts) plus an optional
  CUDA-enabled `Dockerfile.gpu`.
- **GHCR publishing workflow** with multi-arch builds
  (linux/amd64 + linux/arm64), SBOM, and SLSA provenance attestation.
  CPU and `-gpu` flavors tagged on every release.
- **CI/CD**: Python 3.10/3.11/3.12 matrix, ruff/black/mypy, coverage
  upload, sdist + wheel artifact, weekly CodeQL scan, Dependabot for
  pip / actions / docker.
- **Test suite** with 36 tests (~84% coverage) that mocks the heavy ML
  stack so CI completes in well under a second.
- **Documentation**: rewritten `README.md` with badges and client
  examples, `CHANGELOG.md`, `docs/ARCHITECTURE.md`,
  `docs/DEPLOYMENT.md`, `docs/VERSIONING.md`, refreshed `CONTRIBUTING.md`
  and `SECURITY.md`, GitHub issue / PR templates, CODEOWNERS.
- **Pre-commit** with ruff (lint + format), black, hadolint, large-file
  guard, YAML / TOML / merge-conflict checks.

### Changed

- Source layout moved from `app/` to `src/deepface_api/` (PyPA standard).
- Default OpenCV dependency switched to `opencv-python-headless` for
  smaller containers; `libgl1` ships in the runtime image as a fallback
  in case a transitive `opencv-python` wheel is resolved.
- TensorFlow upper bound relaxed to `<3`, platform-aware
  (`tensorflow-macos` on Apple Silicon, regular `tensorflow` elsewhere).
- Python version support: 3.10, 3.11, 3.12.
- Docker image data volume mounts at `/data/output` (was `/app/output`).

### Fixed

- 404 / 405 responses are now wrapped in the standard error envelope
  (the previous handler registered against `fastapi.HTTPException`
  didn't match Starlette-raised router exceptions).
- `tf-keras` (Keras 2 compatibility layer) is now a declared dependency
  on TF 2.16+. Without it, RetinaFace raised
  `ValueError: requires tf-keras package` on import.
- `libgl1` added to runtime image so containers boot even when
  transitive deps resolve `opencv-python` (the GUI variant) instead of
  the headless wheel we declare.

### Removed

- Top-level `api.py` entry shim — use `deepface-api` console script,
  `python -m deepface_api`, or `uvicorn deepface_api.main:app`.
- `requirements.txt` is no longer the canonical dep manifest (kept as a
  convenience file derived from `pyproject.toml`).

## [1.2.0] - 2026-02-19

Initial public release. Basic FastAPI service with `/analyze`,
`/detect_and_return`, and `/health` endpoints.
