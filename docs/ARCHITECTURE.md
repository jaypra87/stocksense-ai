# Architecture

## Processes

StockSense is three runtime processes sharing two data stores:

1. **Next.js frontend** (Vercel) — App Router, mostly client components for the interactive dashboard, talking to the backend over REST.
2. **FastAPI backend** (Render/Fly, Dockerized) — REST API, ML inference, business logic.
3. **Celery worker + beat** — scheduled alert evaluation.

Shared stores:
- **PostgreSQL** — durable source of truth (users, candles, indicators, predictions, risk/sentiment snapshots, watchlists, alerts, backtests, model artifacts).
- **Redis** — cache (quotes, search, sentiment, metadata) + Celery broker/result backend.

## Backend layering (the core discipline)

```
HTTP request
   │
   ▼
[ Router ]    app/api/v1/*.py      — URLs, validation, error → HTTP mapping. THIN.
   │
   ▼
[ Service ]   app/services/*.py    — business logic. Testable without HTTP.
   │
   ├──► [ Provider ]  app/services/market_data/  — pluggable data sources (interface + DTOs)
   ├──► [ ML ]        app/ml/                     — features, training, registry, explain, backtest
   ├──► [ Database ]  app/db/                      — SQLAlchemy models + session
   └──► [ Cache ]     app/cache/                   — Redis get-or-set
   │
   ▼
[ Schema ]    app/schemas/*.py     — Pydantic response contracts
```

**Rule:** routers stay thin; logic lives in services. This is what makes the same logic reusable from a Celery task (e.g. `alert_service.evaluate_alerts`) and testable in isolation.

## Key design patterns

- **Provider abstraction** — everything above `market_data/` depends only on the `MarketDataProvider` interface + DTOs, never on yfinance. Swapping providers (or using the `fake` provider offline/in tests) changes one env var.
- **Pure feature pipeline** — `services/indicators.py` is pure functions reused by the dashboard *and* the ML models, guaranteeing training features == serving features (no skew).
- **Read-through cache** — `cached_json(redis, key, ttl, producer)` is the primary defense against hammering rate-limited providers.
- **Append-only history** — predictions, risk, and sentiment snapshots accumulate over time, enabling backtests of our own past outputs.
- **Model registry** — trained bundles are versioned joblib files; `model_artifacts` tracks which is active per horizon, so retrain/rollback is a row flip.

## Data flow: a forecast

```
POST /predictions/{ticker}?horizon=7d
  → prediction_service.predict
     → fetch_and_store_candles (provider → DB)
     → compute_indicators (pure)
     → latest_feature_row
     → load active model bundle (registry)
     → classifier.predict_proba → trend + confidence
     → regressor trees → expected return range
     → top_contributions (explain) + uncertainty_note
     → compute_risk (indicators + confidence + sentiment)
     → store Prediction row
  → PredictionOut (+ disclaimer)
```

## Scheduled jobs

Celery beat triggers `check_alerts` every 60s → `alert_service.evaluate_alerts`:
groups active alerts, fetches each ticker's quote/risk once, checks the rule, and
records an `AlertEvent` (with a 6h cooldown per alert).

## Database schema (tables)

`users`, `stocks`, `price_candles` (composite PK), `technical_indicators`,
`predictions`, `risk_snapshots`, `sentiment_snapshots`, `watchlists` (composite PK),
`alerts`, `alert_events`, `backtests`, `model_artifacts`.

Migrations are managed by Alembic (`backend/alembic/versions/`).
