#!/usr/bin/env bash
# Convenience wrapper around `docker compose` for common operations.
set -euo pipefail

cd "$(dirname "$0")"

if ! command -v docker >/dev/null 2>&1; then
    echo "Error: docker is required but not installed." >&2
    exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
    echo "Error: docker compose v2 is required (the legacy 'docker-compose' is not supported)." >&2
    exit 1
fi

DC=(docker compose)

usage() {
    cat <<'USAGE'
deepface-api control script.

Usage: ./run.sh <command>

Commands:
  start         Build (if needed) and start the service in the background.
  stop          Stop the service.
  restart       Restart the service.
  logs          Tail service logs.
  build         Build the image.
  pull          Pull pre-built images from the registry.
  ps            Show service status.
  shell         Open a shell inside the running container.
  test          Run the test suite in a one-shot container.
  gpu           Same as `start` but using the GPU profile (requires NVIDIA toolkit).
  help          Show this help.
USAGE
}

case "${1:-help}" in
start)    "${DC[@]}" up -d --build ;;
stop)     "${DC[@]}" down ;;
restart)  "${DC[@]}" restart ;;
logs)     "${DC[@]}" logs -f ;;
build)    "${DC[@]}" build ;;
pull)     "${DC[@]}" pull ;;
ps)       "${DC[@]}" ps ;;
shell)    "${DC[@]}" exec deepface-api /bin/bash ;;
test)     "${DC[@]}" run --rm deepface-api python -m pytest ;;
gpu)      "${DC[@]}" --profile gpu up -d --build ;;
help|-h|--help) usage ;;
*)        echo "Unknown command: $1" >&2; usage; exit 1 ;;
esac
