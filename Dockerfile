# syntax=docker/dockerfile:1.7

# -----------------------------------------------------------------------------
# Multi-stage build:
#   1. `builder` installs Python deps into an isolated prefix using pip with a
#      shared BuildKit cache mount (no wheels left in final image).
#   2. `runtime` is a slim image containing only what's needed to run uvicorn.
# -----------------------------------------------------------------------------

ARG PYTHON_VERSION=3.11

FROM python:${PYTHON_VERSION}-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=0 \
    PIP_ROOT_USER_ACTION=ignore

# Build tools required to compile transitive native deps (h5py, etc.).
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        g++ \
        libhdf5-dev \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Install dependencies first (better Docker layer cache).
COPY requirements.txt ./
RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    pip install --upgrade pip && \
    pip install --prefix=/install -r requirements.txt

# Install the application itself so console-scripts and importlib metadata work.
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    pip install --prefix=/install --no-deps .

# -----------------------------------------------------------------------------
# Runtime stage: small, no compilers, non-root
# -----------------------------------------------------------------------------
FROM python:${PYTHON_VERSION}-slim-bookworm AS runtime

ARG APP_USER=appuser
ARG APP_UID=10001
# Populated by CI (see .github/workflows/docker.yml). Surfaces via the
# /api/version endpoint to identify the exact build at runtime.
ARG BUILD_SHA=""
ARG BUILD_TIME=""

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TF_CPP_MIN_LOG_LEVEL=2 \
    DEEPFACE_OUTPUT_DIR=/data/output \
    DEEPFACE_BUILD_SHA=${BUILD_SHA} \
    DEEPFACE_BUILD_TIME=${BUILD_TIME}

# Minimal runtime libs for opencv (headless wheel still needs libgomp + libGL deps).
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender1 \
        libhdf5-103-1 \
        curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid ${APP_UID} --shell /bin/bash ${APP_USER}

# Copy installed packages from builder.
COPY --from=builder /install /usr/local

WORKDIR /app
COPY --chown=${APP_USER}:${APP_USER} src ./src

RUN mkdir -p ${DEEPFACE_OUTPUT_DIR} && chown -R ${APP_USER}:${APP_USER} /app /data

USER ${APP_USER}

EXPOSE 8008

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD curl --fail --silent http://127.0.0.1:8008/health || exit 1

# Use the console script installed by pip. `deepface-api` honors env settings.
CMD ["deepface-api"]
