"""Orchestrates backtests: fetch long daily history -> walk-forward -> persist.

Runs synchronously (fast enough with a light forest + capped origins). For very
large universes this would move to a Celery task; the engine is already a plain
function, so that's a thin wrapper away.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.backtest import Backtest
from app.ml.backtest import run_walk_forward
from app.ml.features import HORIZON_DAYS, candles_to_frame
from app.services import stock_service
from app.services.indicators import compute_indicators
from app.services.market_data.base import MarketDataProvider

MODEL_VERSION = "walk_forward_v1"
NOTE = (
    "Walk-forward backtest: each prediction uses only data available before its date. "
    "Returns are non-overlapping. Past performance does not predict future results."
)
DISCLAIMER = "Educational backtest only. Not financial advice."


def run_backtest(
    db: Session, provider: MarketDataProvider, user_id: uuid.UUID, raw_ticker: str, horizon: str
) -> dict:
    if horizon not in HORIZON_DAYS:
        raise ValueError(f"unsupported horizon: {horizon}")
    ticker = stock_service.normalize_ticker(raw_ticker)

    candles = stock_service.fetch_and_store_candles(db, provider, ticker, "5y", "1d")
    ind = compute_indicators(candles_to_frame(candles))
    result = run_walk_forward(ind, horizon)  # may raise NotEnoughDataError

    bt = Backtest(
        user_id=user_id,
        ticker=ticker,
        horizon=horizon,
        model_version=MODEL_VERSION,
        start_date=result["start_date"],
        end_date=result["end_date"],
        status="completed",
        metrics_json=result["metrics"],
        chart_data_json=result["chart_data"],
    )
    db.add(bt)
    db.commit()
    db.refresh(bt)
    return _out(bt)


def get_backtest(db: Session, user_id: uuid.UUID, backtest_id: uuid.UUID) -> dict | None:
    bt = db.get(Backtest, backtest_id)
    if bt is None or bt.user_id != user_id:
        return None
    return _out(bt)


def list_backtests(db: Session, user_id: uuid.UUID, limit: int = 50) -> list[dict]:
    rows = db.execute(
        select(Backtest)
        .where(Backtest.user_id == user_id)
        .order_by(Backtest.created_at.desc())
        .limit(limit)
    ).scalars().all()
    return [_summary(bt) for bt in rows]


def _out(bt: Backtest) -> dict:
    return {
        "id": str(bt.id),
        "ticker": bt.ticker,
        "horizon": bt.horizon,
        "model_version": bt.model_version,
        "start_date": bt.start_date,
        "end_date": bt.end_date,
        "status": bt.status,
        "metrics": bt.metrics_json,
        "chart_data": bt.chart_data_json,
        "note": NOTE,
        "disclaimer": DISCLAIMER,
        "created_at": bt.created_at.isoformat() if bt.created_at else None,
    }


def _summary(bt: Backtest) -> dict:
    return {
        "id": str(bt.id),
        "ticker": bt.ticker,
        "horizon": bt.horizon,
        "start_date": bt.start_date,
        "end_date": bt.end_date,
        "metrics": bt.metrics_json,
        "created_at": bt.created_at.isoformat() if bt.created_at else None,
    }
