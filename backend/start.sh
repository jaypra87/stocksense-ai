#!/usr/bin/env sh
# Container entrypoint for production (Render, etc.).
# Runs DB migrations, ensures a demo dataset + trained model exist, then serves.
set -e

echo "[start] running migrations…"
alembic upgrade head

echo "[start] bootstrapping demo data + model…"
# Non-fatal: a transient data-warm failure must not block the server from starting.
python scripts/bootstrap.py || echo "[start] bootstrap warning (continuing)"

echo "[start] launching uvicorn on port ${PORT:-8000}…"
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
