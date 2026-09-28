# Deployment

StockSense deploys as two independent units: the **frontend** on Vercel and the
**backend** (Docker) on Render, backed by managed PostgreSQL (Neon) and Redis (Upstash).
All four have durable free tiers. The public demo runs the `fake` market-data
provider for reliability (Yahoo/yfinance is often blocked on cloud IPs).

## Prerequisites

Free accounts on: [Neon](https://neon.tech) (Postgres), [Upstash](https://upstash.com)
(Redis), [Render](https://render.com) (backend), [Vercel](https://vercel.com) (frontend).

## 1. Database — Neon

1. Create a project; copy the connection string.
2. Convert the scheme to SQLAlchemy's psycopg form:
   `postgresql+psycopg://USER:PASSWORD@HOST/DB?sslmode=require`

## 2. Redis — Upstash

1. Create a Redis database.
2. Copy the `redis://…` (or `rediss://…`) connection URL.

## 3. Backend — Render (Blueprint)

The repo ships a `render.yaml` blueprint and a `backend/start.sh` entrypoint that
runs migrations → binds the port → bootstraps a demo user + trained model
(`scripts/bootstrap.py`) in the background.

1. Render → **New → Blueprint** → select this repo. It reads `render.yaml`.
2. Set the three `sync:false` env vars in the dashboard:
   - `DATABASE_URL` → the Neon string from step 1
   - `REDIS_URL` → the Upstash URL from step 2
   - `CORS_ORIGINS` → your Vercel URL (fill in after step 4, e.g. `https://stocksense-ai.vercel.app`)
   - (`JWT_SECRET` is auto-generated; `MARKET_DATA_PROVIDER`, `BCRYPT_ROUNDS` and
     `ENVIRONMENT=production` are preset.)
3. Deploy. Health check: `/api/v1/health`.
4. Copy the backend URL (e.g. `https://stocksense-backend.onrender.com`).

> Render's free web service spins down after ~15 min idle, so the first request
> after idle waits for a container start. The entrypoint only blocks on
> migrations before serving — the demo-data warm and model training run in the
> background — so that wait is the platform's, not the app's. Set
> `SKIP_BOOTSTRAP=1` to skip the background work entirely.

### If the deployment misbehaves

`GET /api/v1/health/deep` reports each dependency separately and always answers
`200`, so a broken one is visible instead of hidden behind a generic error:

```json
{"status": "degraded", "postgres": "ok", "redis": "unavailable"}
```

- **`redis: unavailable`** — usually `REDIS_URL` unset or pointed at an expired
  free-tier instance. The app stays correct without it (the cache fails open),
  but every request re-fetches from the provider. Note Upstash needs the TLS
  form, `rediss://`, not `redis://`.
- **`postgres: unavailable`** — check `DATABASE_URL`. Any of `postgres://`,
  `postgresql://` or `postgresql+psycopg://` is accepted.
- **Slow logins on a small instance** — bcrypt dominates the request. Lower
  `BCRYPT_ROUNDS` (10–15, default 12; each step down is ~2x faster). Existing
  passwords keep working: bcrypt stores the cost inside each hash.
- **Blank price/profile but working charts** — Yahoo refuses its
  crumb-authenticated endpoints (quote, profile, news, search) from datacenter
  IPs while the chart endpoint keeps serving. The provider falls back to
  candle-derived values, so pages still render; set `MARKET_DATA_PROVIDER=fake`
  if you'd rather show fully synthetic data.

## 4. Frontend — Vercel

1. Vercel → **Add New → Project** → import the repo.
2. Set **Root Directory** to `frontend`.
3. Environment variables:
   - `NEXT_PUBLIC_API_URL` = `<your-render-backend-url>/api/v1`
   - `NEXT_PUBLIC_DEMO_MODE` = `true`
4. Deploy. Copy the Vercel URL.
5. Go back to Render and set `CORS_ORIGINS` to that Vercel URL; redeploy the backend.

## 5. Verify

- `GET https://<backend>/api/v1/health` → `{"status":"ok"}`
- Open the Vercel URL → log in with the seeded demo account
  (`demo@stocksense.ai` / `demopassword123`) → search a ticker → forecast, risk,
  sentiment, indicators, and backtest all render.

## Scheduled alerts (optional, paid)

Render has no free background-worker tier, so the `render.yaml` omits the Celery
worker + beat — alerts can be created but won't auto-fire. To enable them, uncomment
the worker blocks in `render.yaml` (they need a paid plan) with the same
`DATABASE_URL` / `REDIS_URL` / `MARKET_DATA_PROVIDER` env vars.

## Real market data (optional)

Swap `MARKET_DATA_PROVIDER` to a keyed provider and add a concrete provider class
under `app/services/market_data/` (the abstraction makes this a one-file change).
yfinance works locally but is unreliable from datacenter IPs.

## Local Docker

```bash
cp .env.example .env
docker compose up --build
```

## Production checklist

- [ ] `JWT_SECRET` is a strong generated value (Render does this).
- [ ] `CORS_ORIGINS` is restricted to the real Vercel origin.
- [ ] Neon + Upstash URLs set; migrations applied on boot (`start.sh`).
- [ ] A model trained on first boot (`bootstrap.py`).
- [ ] `NEXT_PUBLIC_API_URL` points at the backend `/api/v1`.
