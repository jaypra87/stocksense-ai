# StockSense AI

Production-style, AI-powered stock analytics platform — live market data, technical indicators, ML trend forecasts, news sentiment, risk scoring, watchlists, alerts, and walk-forward backtesting in one dashboard.

> ⚠️ **Educational project only. Not financial advice.** Forecasts are probabilistic and frequently wrong. The baseline models often do not beat naive baselines (by design — see [Model methodology](#model-methodology)). Do not make trading decisions based on this app.

---

## Problem statement

Retail investors and students are handed either black-box "buy/sell" signals with no explanation, or raw data with no interpretation. StockSense AI takes a third path: **interpretable, uncertainty-aware analytics** — every forecast comes with a confidence score, an expected range, a plain-English explanation of the driving factors, a transparent risk breakdown, and honest backtested performance against baselines.

## Features

- **Ticker search & validation** — autocomplete with exchange-suffix support (`AAPL`, `BRK-B`, `VFV.TO`).
- **Live quotes & historical charts** — 1D–5Y ranges, candle persistence, volume overlay.
- **Technical indicators** — SMA/EMA, RSI, MACD, Bollinger Bands, volatility, drawdown, volume spikes.
- **ML forecasts** — 1d/7d/30d trend (bullish/bearish/neutral), confidence, expected price range.
- **Explainability** — per-prediction signed factor attribution + calibration language.
- **Risk engine** — transparent 0–100 composite (volatility, drawdown, volume, trend, model uncertainty, sentiment).
- **News sentiment** — headline classification + narrative summary, fed back into risk.
- **Watchlists & alerts** — saved tickers, alert rules, scheduled checks, triggered history.
- **Backtesting** — walk-forward, no-lookahead, vs. naive baselines, with an equity curve.
- **Model transparency** — data sources, feature list, model metrics, limitations, disclaimer.

## Architecture

```
        Browser
           │ HTTPS
           ▼
   ┌───────────────┐        ┌──────────────────────────┐
   │ Next.js (Vercel)│ ─────►│  FastAPI backend         │
   │ App Router + TS │  REST │  thin routers → services │
   └───────────────┘        │  ML inference (sklearn)  │
                            └───────┬───────────┬──────┘
                                    │           │
                            ┌───────▼──┐   ┌────▼─────┐
                            │ Postgres │   │  Redis   │
                            │ (truth)  │   │ (cache)  │
                            └───────▲──┘   └────▲─────┘
                                    │           │
                            ┌───────┴───────────┴──────┐
                            │  Celery worker + beat     │
                            │  (scheduled alert checks) │
                            └───────────┬──────────────┘
                                        │
                            ┌───────────▼──────────────┐
                            │ Market-data providers     │
                            │ yfinance / fake (offline) │
                            └───────────────────────────┘
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full breakdown.

## Tech stack

| Layer | Tools |
| --- | --- |
| Frontend | Next.js (App Router), TypeScript, Tailwind, React Query, Recharts |
| Backend | FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2 |
| Database | PostgreSQL |
| Cache / jobs | Redis, Celery (worker + beat) |
| ML | pandas, NumPy, scikit-learn (RandomForest) |
| Auth | JWT (PyJWT) + bcrypt |
| Deploy | Vercel (frontend) + Render/Fly (backend, Dockerized) |

## Quick start

### Option A — Docker (parity with production)

```bash
cp .env.example .env
docker compose up --build
# backend  → http://localhost:8000/api/v1/health
# frontend → cd frontend && npm install && npm run dev
```

### Option B — Bare metal (no Docker; faster inner loop)

Requires local PostgreSQL + Redis.

```bash
# 1. Database
createdb stocksense   # or psql: CREATE DATABASE stocksense;

# 2. Backend
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
alembic upgrade head
MARKET_DATA_PROVIDER=fake python scripts/seed.py    # demo user + data + model
uvicorn app.main:app --reload --port 8000

# 3. Frontend (separate terminal)
cd frontend
cp .env.example .env.local
npm install
npm run dev    # http://localhost:3000

# 4. (Optional) Scheduled alert checks
cd backend && source .venv/bin/activate
MARKET_DATA_PROVIDER=fake celery -A app.workers.celery_app worker --loglevel=info   # one terminal
MARKET_DATA_PROVIDER=fake celery -A app.workers.celery_app beat   --loglevel=info   # another
```

**Demo login** (after seeding): `demo@stocksense.ai` / `demopassword123`

### Market data providers

Set `MARKET_DATA_PROVIDER` in `backend/.env`:
- `fake` — deterministic synthetic data, no network, no API key. Great for offline dev and tests.
- `yfinance` — real Yahoo Finance data, no API key required.

The provider is an abstraction (`app/services/market_data/`); adding Polygon/Finnhub is one new file.

## Model methodology

Two `RandomForest` models per horizon (1d/7d/30d): a **classifier** for trend direction and a **regressor** for expected return. Features are scale-free (price/MA ratios, RSI, MACD, volatility, lagged returns) and pooled across many tickers. Labels are forward returns over the horizon.

- **Confidence** = the classifier's class probability.
- **Expected range** = the spread across the regressor's trees (honest uncertainty, not a point estimate).
- **Backtesting** = walk-forward: every prediction trains only on data before its date, origins are non-overlapping, and results are compared to naive baselines (majority-class, persistence, zero-return).

**Why predictions are uncertain (and often wrong):** markets are near-efficient; short-horizon direction is close to a coin flip. On synthetic random-walk data the models correctly fail to beat baselines. This honesty *is the product* — see the in-app Model Transparency page and [docs/ML_METHODOLOGY.md](docs/ML_METHODOLOGY.md).

## Testing

```bash
cd backend && source .venv/bin/activate
pytest            # unit + API tests (indicators, ML features, risk, sentiment, auth, backtest, …)
ruff check app/   # lint
```

```bash
cd frontend
npm run typecheck && npm run build
```

## Project layout

```
stocksense/
├── backend/    FastAPI app, services, ML, Celery workers, Alembic migrations, tests
├── frontend/   Next.js App Router, components, hooks, typed API client
├── docs/       ARCHITECTURE.md, ML_METHODOLOGY.md, DEPLOYMENT.md
└── docker-compose.yml
```

## Deployment

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) — Dockerized backend on Render/Fly, frontend on Vercel, with environment variables and managed Postgres + Redis.

## Known limitations

- Baseline ML models are not expected to be profitable; this is a demonstration of an end-to-end, *honest* ML system, not a trading edge.
- Sentiment uses a lexicon classifier (FinBERT/LLM is a documented upgrade).
- yfinance is rate-limited and unofficial; production should use a paid provider.
- JWT is stored in `localStorage` (XSS trade-off vs httpOnly cookies; acceptable for an educational SPA).

## Disclaimer

For educational purposes only. Not financial advice. Predictions are probabilistic and may be wrong. Do not store brokerage credentials or make trading decisions based on this app.


