#!/usr/bin/env sh
# render_start.sh — entrypoint used by Render when not running via Docker.
# Only needed for native (non-Docker) Render runtimes.
set -e

export PYTHONUNBUFFERED=1
export PORT="${PORT:-8080}"

# Ensure the data directory exists (Render persistent disk is mounted at /app/data)
mkdir -p data

exec uvicorn app:app \
  --host 0.0.0.0 \
  --port "$PORT" \
  --workers 1 \
  --timeout-keep-alive 120
