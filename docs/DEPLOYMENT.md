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
2. Set the `sync:false` env vars in the dashboard:
   - `DATABASE_URL` → the Neon string from step 1
   - `REDIS_URL` → the Upstash URL from step 2 (`rediss://`, TLS)
   - `CORS_ORIGINS` → your Vercel URL (fill in after step 4, e.g. `https://stocksense-ai.vercel.app`)
   - `EMAIL_ENCRYPTION_KEY` → `openssl rand -hex 32`. **Required**; the app refuses
     to boot in production without it. Emails are encrypted with it, so back it
     up: losing it makes existing addresses unreadable.
   - `PROXY_SHARED_SECRET` → `openssl rand -hex 32`; the same value goes into
     Vercel as `API_PROXY_SECRET` (step 4).
   - `TURNSTILE_SECRET_KEY` → from Cloudflare (step 6). Optional; without it bot
     protection is off and the log says so.
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

The browser never talks to Render directly. A route handler at
`frontend/app/api/v1/[...path]/route.ts` proxies `/api/v1/*` on the Vercel domain
to the backend, which is what makes the session cookie first-party
(`HttpOnly; Secure; SameSite=Lax`) and keeps the backend address out of the
browser.

1. Vercel → **New Project** → import the repo → root directory `frontend`.
2. Environment variables:
   - `BACKEND_URL` → the Render URL from step 3, **without** `/api/v1`
     (e.g. `https://stocksense-backend.onrender.com`)
   - `API_PROXY_SECRET` → the same value as `PROXY_SHARED_SECRET` on Render
   - `NEXT_PUBLIC_SITE_URL` → the Vercel URL (for SEO metadata)
   - `NEXT_PUBLIC_DEMO_MODE` → `true` (shows the live-demo banner)
   - `NEXT_PUBLIC_TURNSTILE_SITE_KEY` → from Cloudflare (step 6); optional
3. Deploy.
4. Go back to Render and set `CORS_ORIGINS` to the Vercel URL; redeploy the backend.
   `CORS_ORIGINS` doubles as the allow-list for the Origin check on
   state-changing requests, so list **every** origin the app is served from
   (comma-separated): the production domain and, if you use them, Vercel
   preview URLs. A write from an unlisted origin gets a 403 "Cross-site request
   refused", which the app shows on its session screen.

## 6. Bot protection — Cloudflare Turnstile (recommended)

1. https://dash.cloudflare.com → **Turnstile** → **Add site**. Hostnames: the
   Vercel domain (and `localhost` for local testing). Widget mode: *Managed*.
2. Copy the **site key** → Vercel `NEXT_PUBLIC_TURNSTILE_SITE_KEY`; the
   **secret key** → Render `TURNSTILE_SECRET_KEY`. Redeploy both.
3. Sign-in and save-account now require a passed check, and a network that
   exhausts its guest-session allowance gets a challenge instead of a flat 429.

## 7. Keep the free backend awake (recommended)

`.github/workflows/keepalive.yml` pings the API every 10 minutes. In the GitHub
repo: **Settings → Secrets and variables → Actions → Variables** → add
`HEALTH_URL` = `https://<vercel-domain>/api/v1/health`. Going through Vercel
warms both hops. GitHub can delay scheduled jobs, so this shortens cold starts
dramatically without promising zero.

## 5. Verify

- `GET https://<backend>/api/v1/health` → `{"status":"ok"}`
- `GET https://<vercel>/api/v1/health` → `{"status":"ok"}` (through the proxy)
- Open the Vercel URL → **Open dashboard** → you are in as a guest with no form
  → search a ticker → forecast, risk, sentiment, indicators, and backtest all
  render. The header's **Save account** turns the guest into an account; **Sign
  in** with the seeded demo account (`demo@stocksense.ai` / `demopassword123`)
  exercises the merge path.
- In the browser devtools, the `ss_session` cookie is `HttpOnly`, `Secure`,
  `SameSite=Lax`, on the Vercel domain.

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
- [ ] `EMAIL_ENCRYPTION_KEY` set on Render and backed up somewhere safe.
- [ ] `PROXY_SHARED_SECRET` (Render) equals `API_PROXY_SECRET` (Vercel).
- [ ] `CORS_ORIGINS` is restricted to the real Vercel origin.
- [ ] Neon + Upstash URLs set; `/api/v1/health/deep` reports both `ok`.
- [ ] Migrations applied on boot (`start.sh`); a model trained (`bootstrap.py`).
- [ ] `BACKEND_URL` on Vercel points at the Render service root (no `/api/v1`).
- [ ] Turnstile keys set on both sides (`TURNSTILE_SECRET_KEY`, `NEXT_PUBLIC_TURNSTILE_SITE_KEY`).
- [ ] GitHub repository variable `HEALTH_URL` set so the keep-alive workflow runs.
