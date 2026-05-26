# Architecture

This document explains how `deepface-api` is structured, how a request
flows through the system, and the trade-offs behind each layer.

## High-level diagram

```text
                  ┌────────────────────────────┐
HTTP client ─►   │   uvicorn (ASGI server)    │
                  └─────────────┬──────────────┘
                                │
                  ┌─────────────▼──────────────┐
                  │   FastAPI app              │
                  │   create_app(settings)     │
                  └─────────────┬──────────────┘
                                │ middlewares
                                ▼
                   RequestIDMiddleware ─► CORSMiddleware
                                │
                                ▼
                ┌───────────────────────────────┐
                │  /api/v1 router               │
                │   ├─ health.py                │
                │   └─ analyze.py               │
                └───────────────┬───────────────┘
                                │ DI: get_settings()
                                ▼
                ┌───────────────────────────────┐
                │  services/                    │
                │   ├─ uploads.py  (cv2 decode) │
                │   └─ vision.py   (RF + DF)    │
                └───────────────┬───────────────┘
                                │ run_in_threadpool
                                ▼
                  RetinaFace.detect_faces(img)
                  DeepFace.analyze(crop, …)
```

## Package layout

```text
src/deepface_api/
├── __init__.py          # version, importlib metadata + fallback
├── __main__.py          # `python -m deepface_api` entrypoint
├── _version.py          # single source of truth for the version
├── config.py            # pydantic-settings + legacy env aliases
├── logging.py           # text / JSON log formatter
├── middleware.py        # RequestIDMiddleware (also logs latency)
├── exceptions.py        # APIError hierarchy + handlers
├── main.py              # create_app() factory + module-level `app`
├── schemas/             # Pydantic v2 response models
│   ├── analysis.py
│   └── errors.py
├── services/            # Business logic
│   ├── uploads.py
│   └── vision.py
└── api/
    └── v1/              # First public API version
        ├── router.py
        ├── health.py
        └── analyze.py
```

The `src/` layout is the PyPA-recommended packaging layout: it forces
tests to import via the installed package rather than ad-hoc relative
imports, which makes packaging / wheel verification more reliable.

## Request lifecycle

1. **Uvicorn** receives the HTTP request and forwards it to the ASGI
   `app` instance built by `create_app()`.
2. **`RequestIDMiddleware`** assigns or echoes an `X-Request-ID` header,
   stores it in `request.state.request_id`, and records start/end latency
   plus status code in the structured logs.
3. **`CORSMiddleware`** applies the configured policy.
4. The matching **router handler** runs. `get_settings()` is injected via
   FastAPI's `Depends`, which makes settings easy to override in tests.
5. The handler delegates to **`services/uploads.py`** to validate and
   decode the upload (raising `InvalidUploadError` or
   `UploadTooLargeError` on bad input).
6. **`services/vision.py`** runs the heavy ML calls on the asyncio
   thread pool via `starlette.concurrency.run_in_threadpool` so the
   event loop stays responsive.
7. If `save_render=true`, an annotated copy is written via OpenCV to
   `settings.output_dir`.
8. The response is serialized through the **Pydantic v2 `AnalyzeResponse`**
   schema for type-safe JSON output, or returned as a `image/jpeg`
   response for `/detect_and_return`.
9. **`exceptions.register_exception_handlers()`** converts any uncaught
   `APIError`, `HTTPException`, or `RequestValidationError` into a
   uniform JSON envelope.

## Design choices

### Versioned API with backwards-compatible aliases

The v1 router is mounted at `/api/v1` (canonical) and again at `/` with
`include_in_schema=False`. Existing clients hitting `/analyze` keep
working; new clients use the versioned path, and the OpenAPI document
only advertises the canonical paths.

### Settings via pydantic-settings + env aliases

`Settings` reads from `DEEPFACE_*` env vars and an optional `.env` file.
Legacy unprefixed vars (`SERVER_PORT`, etc.) are aliased into the new
prefix in `get_settings()` so old deployment configurations continue to
work without code changes.

### Threadpool offload for ML calls

Both `RetinaFace.detect_faces` and `DeepFace.analyze` are synchronous
and CPU/GPU heavy. Wrapping them with `run_in_threadpool` keeps the
asyncio event loop responsive — but a single process is still
single-threaded relative to those ML calls because of the GIL + native
locks inside TensorFlow. For high QPS, run multiple uvicorn workers or
scale horizontally.

### Multi-stage Docker build

- The **builder** stage installs build tools + Python wheels into
  `/install`. BuildKit cache mounts (`--mount=type=cache,target=…`)
  preserve apt and pip caches between builds.
- The **runtime** stage starts from `python:3.11-slim-bookworm`, copies
  the prebuilt site-packages, drops privileges to `appuser` (uid
  10001), exposes 8008, and uses `curl` against `/health` as its
  `HEALTHCHECK`. The image stays around ~1 GB even with TensorFlow.

A GPU variant (`Dockerfile.gpu`) uses an `nvidia/cuda:*-cudnn9-runtime`
base instead.

### Keras 2 compatibility for ML deps

`retinaface` and `deepface` still target the Keras 2 API. TensorFlow
2.16 switched to Keras 3 by default, so on those versions we install
`tf-keras` (the Keras 2 compatibility package) as a regular runtime
dependency. The legacy Apple-Silicon `tensorflow-macos` wheel stays on
TF 2.15 / Keras 2 and doesn't need it. This is wired up in
`pyproject.toml` and `requirements.txt` via environment markers.

## Testing strategy

- **Unit tests** mock `detect_faces` / `analyze_single_face` so the
  entire suite runs without TensorFlow, RetinaFace, or DeepFace
  installed — making CI fast and matrix-friendly (3.10 / 3.11 / 3.12).
- **Integration tests** that exercise the real models can be added
  under a `@pytest.mark.integration` marker and gated by a separate
  workflow (currently optional).
- `conftest.py` exposes reusable fixtures: a synthetic JPEG payload, a
  per-test `Settings` instance (writing to `tmp_path`), and a vision
  mock.

## Extension points

- **New endpoints** → drop a new module under `src/deepface_api/api/v1/`
  and include it from `router.py`.
- **New API version** → create `src/deepface_api/api/v2/` with the same
  layout and mount it at `/api/v2` in `main.create_app()`. The v1
  router keeps serving its prefix during the deprecation window.
- **Alternative detector / analyzer** → swap implementations in
  `services/vision.py`. The handlers depend only on the function
  shapes (`detect_faces`, `analyze_single_face`).
- **Auth, rate limiting, metrics** → add as additional ASGI middlewares
  in `main.create_app()`. Prometheus / OTel exporters compose cleanly
  with the existing stack.
