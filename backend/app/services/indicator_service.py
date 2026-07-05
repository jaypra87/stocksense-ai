"""Orchestrates indicators: load daily candles -> compute -> persist -> respond.

Indicators are always computed on DAILY candles. We fetch a long lookback
(enough to warm up SMA-100 etc.) regardless of the requested range, then return
only the requested window. This keeps the latest values correct even for short
ranges, where a naive fetch wouldn't have enough history.
"""

import math
from datetime import UTC, datetime

import pandas as pd
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.db.models.technical_indicator import TechnicalIndicator
from app.services import stock_service
from app.services.indicators import compute_indicators
from app.services.market_data.base import MarketDataProvider

# Daily candles to fetch for computation (warmup-inclusive).
_LOOKBACK = {
    "1d": "1y",
    "5d": "1y",
    "1m": "1y",
    "6m": "1y",
    "ytd": "1y",
    "1y": "2y",
    "5y": "5y",
}

# Trailing daily points to return for each range.
_RANGE_POINTS = {"1d": 2, "5d": 5, "1m": 22, "6m": 126, "1y": 252, "5y": 1300}

# Columns we persist and serialize (everything compute_indicators adds).
_NUMERIC_COLS = [
    "sma_7", "sma_30", "sma_100", "ema_20", "rsi_14",
    "macd", "macd_signal", "macd_hist",
    "bollinger_mid", "bollinger_upper", "bollinger_lower",
    "volatility_30", "drawdown", "daily_return", "relative_volume",
]


def get_indicators(
    db: Session, provider: MarketDataProvider, raw_ticker: str, range_: str = "1y"
) -> dict:
    ticker = stock_service.normalize_ticker(raw_ticker)
    period = _LOOKBACK.get(range_, "1y")

    candles = stock_service.fetch_and_store_candles(db, provider, ticker, period, "1d")
    df = _candles_to_df(candles)
    enriched = compute_indicators(df)

    _store_indicators(db, ticker, enriched)

    window = _slice_range(enriched, range_)
    return {
        "ticker": ticker,
        "range": range_,
        "interval": "1d",
        "latest": latest_snapshot(enriched),
        "signals": signals(enriched),
        "series": [_row_to_point(ts, row) for ts, row in window.iterrows()],
    }


# --- helpers ---


def _candles_to_df(candles: list) -> pd.DataFrame:
    df = pd.DataFrame(
        {
            "timestamp": [c.timestamp for c in candles],
            "open": [c.open for c in candles],
            "high": [c.high for c in candles],
            "low": [c.low for c in candles],
            "close": [c.close for c in candles],
            "volume": [c.volume or 0 for c in candles],
        }
    ).set_index("timestamp")
    return df.sort_index()


def _slice_range(df: pd.DataFrame, range_: str) -> pd.DataFrame:
    if range_ == "ytd":
        year = datetime.now(UTC).year
        return df[df.index.map(lambda ts: ts.year == year)]
    return df.tail(_RANGE_POINTS.get(range_, 252))


def _f(value: object) -> float | None:
    """NaN/inf -> None, otherwise a rounded float for JSON."""
    if value is None:
        return None
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(v) or math.isinf(v):
        return None
    return round(v, 4)


def _row_to_point(ts: datetime, row: pd.Series) -> dict:
    point = {"timestamp": ts.isoformat()}
    for col in _NUMERIC_COLS:
        point[col] = _f(row[col])
    return point


def latest_snapshot(df: pd.DataFrame) -> dict:
    """Latest indicator values from an already-enriched DataFrame."""
    last = df.iloc[-1]
    out = {"timestamp": df.index[-1].isoformat(), "close": _f(last["close"])}
    for col in _NUMERIC_COLS:
        out[col] = _f(last[col])
    # Max drawdown across the full computed series (a useful summary stat).
    out["max_drawdown"] = _f(df["drawdown"].min())
    return out


def signals(df: pd.DataFrame) -> dict:
    """Derived signals from an already-enriched DataFrame."""
    last = df.iloc[-1]
    rsi_val = _f(last["rsi_14"])
    close = _f(last["close"])
    sma_30 = _f(last["sma_30"])
    sma_100 = _f(last["sma_100"])
    macd_val = _f(last["macd"])
    macd_sig = _f(last["macd_signal"])

    rsi_zone = None
    if rsi_val is not None:
        rsi_zone = "overbought" if rsi_val >= 70 else "oversold" if rsi_val <= 30 else "neutral"

    trend = None
    if sma_30 is not None and sma_100 is not None:
        trend = "up" if sma_30 >= sma_100 else "down"

    macd_bullish = None
    if macd_val is not None and macd_sig is not None:
        macd_bullish = macd_val > macd_sig

    return {
        "rsi_zone": rsi_zone,
        "macd_bullish": macd_bullish,
        "above_sma_30": (close > sma_30) if (close is not None and sma_30 is not None) else None,
        "above_sma_100": (close > sma_100) if (close is not None and sma_100 is not None) else None,
        "trend": trend,
        "volume_spike": _bool_or_none(last["volume_spike"]),
    }


def _bool_or_none(value: object) -> bool | None:
    return bool(value) if pd.notna(value) else None


def _store_indicators(db: Session, ticker: str, df: pd.DataFrame) -> None:
    rows = []
    for ts, row in df.iterrows():
        record = {"ticker": ticker, "timestamp": ts}
        for col in _NUMERIC_COLS:
            record[col] = _f(row[col])
        record["volume_spike"] = _bool_or_none(row["volume_spike"])
        rows.append(record)

    if not rows:
        return

    stmt = pg_insert(TechnicalIndicator).values(rows)
    update_cols = {c: getattr(stmt.excluded, c) for c in [*_NUMERIC_COLS, "volume_spike"]}
    stmt = stmt.on_conflict_do_update(
        index_elements=["ticker", "timestamp"], set_=update_cols
    )
    db.execute(stmt)
    db.commit()
