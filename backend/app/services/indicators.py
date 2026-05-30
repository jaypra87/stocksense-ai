"""Technical-indicator math. Pure functions over pandas Series/DataFrames.

This module has NO knowledge of the DB, cache, or HTTP — it just transforms
numbers. That makes it trivial to unit test, and it's the same feature pipeline
the ML models will consume in Phase 5.

Conventions:
- Input is a DataFrame indexed by timestamp with columns: open, high, low,
  close, volume (the shape our CandleDTOs produce).
- All indicators are computed on the `close` series unless noted.
- Early rows (before an indicator's window fills) are NaN; callers convert
  NaN -> null when serializing.
"""

import numpy as np
import pandas as pd

TRADING_DAYS = 252


def sma(series: pd.Series, window: int) -> pd.Series:
    """Simple moving average."""
    return series.rolling(window=window).mean()


def ema(series: pd.Series, span: int) -> pd.Series:
    """Exponential moving average (more weight on recent values)."""
    return series.ewm(span=span, adjust=False).mean()


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index using Wilder's smoothing (alpha = 1/period).

    RSI oscillates 0-100: >70 conventionally "overbought", <30 "oversold".
    """
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def macd(
    close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """MACD line, signal line, and histogram.

    MACD = EMA(fast) - EMA(slow); signal = EMA(signal) of MACD; hist = MACD - signal.
    """
    macd_line = ema(close, fast) - ema(close, slow)
    signal_line = ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def bollinger(
    close: pd.Series, window: int = 20, num_std: float = 2.0
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Bollinger Bands: (middle, upper, lower).

    Middle is SMA(window); bands sit num_std rolling standard deviations away.
    """
    middle = sma(close, window)
    std = close.rolling(window=window).std()
    upper = middle + num_std * std
    lower = middle - num_std * std
    return middle, upper, lower


def daily_returns(close: pd.Series) -> pd.Series:
    """Simple period-over-period percentage return (as a fraction)."""
    return close.pct_change()


def volatility(close: pd.Series, window: int = 30, annualize: bool = True) -> pd.Series:
    """Rolling standard deviation of returns, optionally annualized, as a percent."""
    vol = daily_returns(close).rolling(window=window).std()
    if annualize:
        vol = vol * np.sqrt(TRADING_DAYS)
    return vol * 100


def drawdown(close: pd.Series) -> pd.Series:
    """Percent decline from the running peak (<= 0). 0 means at an all-time high."""
    running_max = close.cummax()
    return (close / running_max - 1) * 100


def relative_volume(volume: pd.Series, window: int = 20) -> pd.Series:
    """Volume relative to its rolling average. 2.0 means twice the typical volume."""
    avg = volume.rolling(window=window).mean()
    return volume / avg


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of `df` with all indicator columns added."""
    out = df.copy()
    close = out["close"]

    out["sma_7"] = sma(close, 7)
    out["sma_30"] = sma(close, 30)
    out["sma_100"] = sma(close, 100)
    out["ema_20"] = ema(close, 20)
    out["rsi_14"] = rsi(close, 14)

    macd_line, signal_line, hist = macd(close)
    out["macd"] = macd_line
    out["macd_signal"] = signal_line
    out["macd_hist"] = hist

    mid, upper, lower = bollinger(close)
    out["bollinger_mid"] = mid
    out["bollinger_upper"] = upper
    out["bollinger_lower"] = lower

    out["volatility_30"] = volatility(close, 30)
    out["drawdown"] = drawdown(close)
    out["daily_return"] = daily_returns(close)
    out["relative_volume"] = relative_volume(out["volume"])
    out["volume_spike"] = out["relative_volume"] > 2.0

    return out
