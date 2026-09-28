#!/usr/bin/env sh
# Container entrypoint for production (Render, etc.).
#
# Ordering matters for perceived speed. On a free tier the instance is spun down
# after idle, so *every* first visit pays this script's cost before a single
# request is answered. Only migrations genuinely have to finish before we serve
# (they change the schema the handlers read); the demo-data/model bootstrap does
# not, and it is the slow part — it fetches four tickers from the market-data
# provider and retrains the model whenever the artifact is missing, which on an
# ephemeral disk is every single boot. Running it inline used to hold the port
# closed for minutes, which is exactly what made the first login feel hung.
#
# So: migrate, bind the port, and let the bootstrap finish in the background.
set -e

echo "[start] running migrations…"
alembic upgrade head

if [ "${SKIP_BOOTSTRAP:-}" = "1" ]; then
  echo "[start] SKIP_BOOTSTRAP=1 — skipping demo data + model bootstrap"
else
  echo "[start] bootstrapping demo data + model in background…"
  # Non-fatal and off the critical path: a transient data-warm failure must
  # never block or delay the server. Niced so it yields CPU to real requests
  # on small shared-core instances.
  nice -n 10 python scripts/bootstrap.py \
    && echo "[start] bootstrap complete" \
    || echo "[start] bootstrap warning (server unaffected)" &
fi

echo "[start] launching uvicorn on port ${PORT:-8000}…"
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
