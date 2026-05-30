"""Model transparency endpoint (public).

Surfaces data sources, the feature list, registered model versions + their
metrics, methodology, and limitations — everything the Model Transparency page
needs to be honest about how forecasts are produced.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.model_artifact import ModelArtifact
from app.db.session import get_db
from app.ml.features import FEATURE_COLS
from app.schemas.model_info import ModelsOut

router = APIRouter(prefix="/models", tags=["models"])

_FEATURE_DESCRIPTIONS = {
    "ret_close_sma7": "Price relative to its 7-day moving average",
    "ret_close_sma30": "Price relative to its 30-day moving average",
    "ret_close_sma100": "Price relative to its 100-day moving average",
    "ret_sma7_sma30": "Short-term vs medium-term trend (SMA7/SMA30)",
    "ret_close_ema20": "Price relative to its 20-day EMA",
    "rsi": "Relative Strength Index (momentum oscillator)",
    "macd_norm": "MACD line, normalized by price",
    "macd_hist_norm": "MACD histogram, normalized by price",
    "bb_pos": "Position within the Bollinger Bands",
    "volatility": "30-day annualized volatility",
    "drawdown_n": "Decline from the recent peak",
    "rel_volume": "Volume relative to its 20-day average",
    "ret_0": "Most recent daily return",
    "ret_1": "Daily return lagged 1 day",
    "ret_2": "Daily return lagged 2 days",
    "ret_3": "Daily return lagged 3 days",
    "ret_4": "Daily return lagged 4 days",
}

_DATA_SOURCES = [
    "Market data: yfinance (Yahoo Finance) in development; pluggable provider "
    "abstraction supports Polygon/Finnhub in production.",
    "Technical indicators: computed in-house from OHLCV candles (SMA, EMA, RSI, "
    "MACD, Bollinger Bands, volatility, drawdown, volume).",
    "News sentiment: recent headlines classified with a finance-tuned lexicon.",
    "All data is cached and persisted to PostgreSQL; nothing is sourced from "
    "private brokerage accounts.",
]

_METHODOLOGY = (
    "Two RandomForest models per horizon (1d/7d/30d): a classifier for trend "
    "direction and a regressor for expected return. Features are scale-free "
    "(ratios, oscillators) and pooled across many tickers. Labels are forward "
    "returns over the horizon. Confidence is the classifier's class probability; "
    "the expected range is the spread across the regressor's trees. Models are "
    "evaluated with walk-forward backtesting against naive baselines."
)

_LIMITATIONS = [
    "Markets are near-efficient; short-term prediction is inherently uncertain "
    "and these baseline models often do not beat naive baselines.",
    "Forecasts are probabilistic estimates, not guarantees — confidence reflects "
    "model agreement, not certainty.",
    "Training data is limited and does not capture every market regime, news "
    "shock, or macro event.",
    "Backtests use only past data at each point, but past performance does not "
    "predict future results.",
    "This is an educational project, not investment advice.",
]

_DISCLAIMER = "Educational analytics only. Not financial advice. Predictions may be wrong."


@router.get("", response_model=ModelsOut)
def list_models(db: Session = Depends(get_db)) -> dict:
    artifacts = db.execute(
        select(ModelArtifact).order_by(ModelArtifact.trained_at.desc())
    ).scalars().all()

    return {
        "data_sources": _DATA_SOURCES,
        "features": [
            {"name": f, "description": _FEATURE_DESCRIPTIONS.get(f, "")} for f in FEATURE_COLS
        ],
        "models": [
            {
                "model_version": a.model_version,
                "horizon": a.horizon,
                "is_active": a.is_active,
                "trained_at": a.trained_at.isoformat() if a.trained_at else None,
                "metrics": a.metrics_json,
            }
            for a in artifacts
        ],
        "methodology": _METHODOLOGY,
        "limitations": _LIMITATIONS,
        "disclaimer": _DISCLAIMER,
    }
