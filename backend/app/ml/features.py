"""Feature engineering for the ML models.

Reuses the SAME indicator math the dashboard uses (app.services.indicators),
so training features == serving features by construction — no drift.

All features are scale-free (ratios, oscillators, normalized values), which is
what lets us pool many tickers into one global model.

Leakage discipline:
- Every feature at row t uses only data up to and including t.
- Labels are the FORWARD return over the horizon (t -> t+h) and are only used
  as training targets, never as features.
"""

import numpy as np
import pandas as pd

# The model's input columns, in a fixed order. Persisted with each model bundle.
FEATURE_COLS = [
    "ret_close_sma7",
    "ret_close_sma30",
    "ret_close_sma100",
    "ret_sma7_sma30",
    "ret_close_ema20",
    "rsi",
    "macd_norm",
    "macd_hist_norm",
    "bb_pos",
    "volatility",
    "drawdown_n",
    "rel_volume",
    "ret_0",
    "ret_1",
    "ret_2",
    "ret_3",
    "ret_4",
]

HORIZON_DAYS = {"1d": 1, "7d": 7, "30d": 30}

# Forward-return magnitude that separates bullish/bearish from neutral, per horizon.
DIRECTION_THRESHOLD = {"1d": 0.005, "7d": 0.02, "30d": 0.04}


def candles_to_frame(candles: list) -> pd.DataFrame:
    """CandleDTO list -> timestamp-indexed OHLCV DataFrame (sorted)."""
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


def build_feature_frame(indicators_df: pd.DataFrame) -> pd.DataFrame:
    """Derive scale-free features from an indicator-enriched DataFrame."""
    ind = indicators_df
    close = ind["close"]
    band = ind["bollinger_upper"] - ind["bollinger_lower"]

    f = pd.DataFrame(index=ind.index)
    f["ret_close_sma7"] = close / ind["sma_7"] - 1
    f["ret_close_sma30"] = close / ind["sma_30"] - 1
    f["ret_close_sma100"] = close / ind["sma_100"] - 1
    f["ret_sma7_sma30"] = ind["sma_7"] / ind["sma_30"] - 1
    f["ret_close_ema20"] = close / ind["ema_20"] - 1
    f["rsi"] = ind["rsi_14"] / 100
    f["macd_norm"] = ind["macd"] / close
    f["macd_hist_norm"] = ind["macd_hist"] / close
    f["bb_pos"] = (close - ind["bollinger_mid"]) / band
    f["volatility"] = ind["volatility_30"] / 100
    f["drawdown_n"] = ind["drawdown"] / 100
    f["rel_volume"] = ind["relative_volume"]
    f["ret_0"] = ind["daily_return"]
    for k in range(1, 5):
        f[f"ret_{k}"] = ind["daily_return"].shift(k)

    f["close"] = close  # kept for label construction / price ranges, not a feature
    return f.replace([np.inf, -np.inf], np.nan)


def make_training_matrix(
    indicators_df: pd.DataFrame, horizon: str
) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    """Build (X, y_class, y_reg) for one ticker at one horizon.

    y_reg  = forward return over the horizon.
    y_class = 'bullish' / 'bearish' / 'neutral' from that return vs a threshold.
    """
    days = HORIZON_DAYS[horizon]
    threshold = DIRECTION_THRESHOLD[horizon]

    feats = build_feature_frame(indicators_df)
    close = indicators_df["close"]
    fwd_return = close.shift(-days) / close - 1

    y_class = fwd_return.apply(
        lambda r: "bullish" if r > threshold else "bearish" if r < -threshold else "neutral"
    )

    data = feats.assign(y_reg=fwd_return, y_class=y_class).dropna(
        subset=[*FEATURE_COLS, "y_reg"]
    )
    return data[FEATURE_COLS], data["y_class"], data["y_reg"]


def latest_feature_row(indicators_df: pd.DataFrame, feature_cols: list[str]) -> pd.DataFrame:
    """The most recent fully-populated feature row, for inference."""
    feats = build_feature_frame(indicators_df).dropna(subset=feature_cols)
    if feats.empty:
        raise ValueError("not enough history to build a feature row")
    return feats[feature_cols].iloc[[-1]]
