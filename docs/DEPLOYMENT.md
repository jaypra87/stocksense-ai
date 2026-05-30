# Deployment

StockSense deploys as two independent units: the **frontend** to Vercel and the **backend** (Dockerized) to Render/Fly/AWS, backed by managed PostgreSQL + Redis.

## Backend (Render / Fly / AWS)

The backend ships as a container (`backend/Dockerfile`).

**Environment variables:**

| Var | Example | Notes |
| --- | --- | --- |
| `ENVIRONMENT` | `production` | |
| `DATABASE_URL` | `postgresql+psycopg://user:pass@host:5432/stocksense` | managed Postgres |
| `REDIS_URL` | `redis://:pass@host:6379/0` | managed Redis |
| `CORS_ORIGINS` | `https://your-app.vercel.app` | comma-separated |
| `JWT_SECRET` | *(long random string)* | **must change from default** |
| `MARKET_DATA_PROVIDER` | `yfinance` | or a paid provider |
| `POLYGON_API_KEY` / `FINNHUB_API_KEY` | … | if using those providers |

**Steps:**

1. Provision managed PostgreSQL and Redis; copy their connection URLs.
2. Deploy the backend image. Set the env vars above.
3. Run migrations on release: `alembic upgrade head`.
4. Train an initial model: `python scripts/train_baseline.py` (or `scripts/seed.py` for a full demo).
5. Health check path: `/api/v1/health/deep` (verifies Postgres + Redis).

**Worker + beat** (scheduled alerts) run as separate processes/services from the same image:

```
celery -A app.workers.celery_app worker --loglevel=info
celery -A app.workers.celery_app beat   --loglevel=info
```

## Frontend (Vercel)

1. Import the repo; set the root directory to `frontend/`.
2. Set `NEXT_PUBLIC_API_URL=https://<your-backend-host>/api/v1`.
3. Deploy. Vercel auto-detects Next.js (build: `next build`).
4. Add the Vercel URL to the backend's `CORS_ORIGINS`.

## Local Docker

```bash
cp .env.example .env
docker compose up --build
```

`docker-compose.yml` brings up Postgres, Redis, and the backend (with healthchecks). The frontend runs on the host via `npm run dev` (it deploys to Vercel separately).

## Production checklist

- [ ] `JWT_SECRET` rotated to a strong random value.
- [ ] `CORS_ORIGINS` restricted to the real frontend origin(s).
- [ ] Managed Postgres + Redis with backups.
- [ ] Migrations applied (`alembic upgrade head`).
- [ ] At least one model trained (`scripts/train_baseline.py`).
- [ ] Worker + beat running for alerts.
- [ ] A paid market-data provider (yfinance is unofficial and rate-limited).
- [ ] Logs/error monitoring wired up (request logging is built in).
