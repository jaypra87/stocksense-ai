import numpy as np
import pandas as pd

from app.services.indicators import (
    bollinger,
    compute_indicators,
    drawdown,
    ema,
    macd,
    relative_volume,
    rsi,
    sma,
)


def test_sma_known_values() -> None:
    s = pd.Series([1, 2, 3, 4, 5], dtype=float)
    result = sma(s, 2).tolist()
    assert np.isnan(result[0])
    assert result[1:] == [1.5, 2.5, 3.5, 4.5]


def test_ema_reacts_faster_than_sma() -> None:
    s = pd.Series([10] * 10 + [20] * 10, dtype=float)
    # After the jump, EMA(5) should be closer to the new level than SMA(5).
    assert ema(s, 5).iloc[12] > sma(s, 5).iloc[12]


def test_rsi_bounds_and_extremes() -> None:
    rising = pd.Series(range(1, 60), dtype=float)
    falling = pd.Series(range(60, 1, -1), dtype=float)
    r_up = rsi(rising).iloc[-1]
    r_down = rsi(falling).iloc[-1]
    assert 0 <= r_up <= 100 and 0 <= r_down <= 100
    assert r_up > 80  # straight up -> very high RSI
    assert r_down < 20  # straight down -> very low RSI


def test_macd_histogram_is_macd_minus_signal() -> None:
    s = pd.Series(np.linspace(100, 120, 80))
    macd_line, signal_line, hist = macd(s)
    assert np.allclose((macd_line - signal_line).dropna(), hist.dropna())


def test_bollinger_band_ordering() -> None:
    s = pd.Series(np.random.default_rng(0).normal(100, 5, 100))
    mid, upper, lower = bollinger(s)
    valid = mid.dropna().index
    assert (upper.loc[valid] >= mid.loc[valid]).all()
    assert (mid.loc[valid] >= lower.loc[valid]).all()


def test_drawdown_is_non_positive_and_zero_at_peak() -> None:
    s = pd.Series([10, 12, 15, 11, 9], dtype=float)
    dd = drawdown(s)
    assert (dd <= 1e-9).all()
    assert dd.iloc[2] == 0.0  # 15 is the running peak


def test_relative_volume_around_one_for_flat_volume() -> None:
    v = pd.Series([1000] * 30, dtype=float)
    rv = relative_volume(v).dropna()
    assert np.allclose(rv, 1.0)


def test_compute_indicators_adds_all_columns() -> None:
    n = 150
    rng = np.random.default_rng(1)
    close = 100 + np.cumsum(rng.normal(0, 1, n))
    df = pd.DataFrame(
        {
            "open": close,
            "high": close + 1,
            "low": close - 1,
            "close": close,
            "volume": rng.integers(1_000_000, 5_000_000, n),
        },
        index=pd.date_range("2024-01-01", periods=n, freq="D", tz="UTC"),
    )
    out = compute_indicators(df)
    for col in ["sma_7", "sma_30", "sma_100", "ema_20", "rsi_14", "macd",
                "bollinger_upper", "volatility_30", "drawdown", "volume_spike"]:
        assert col in out.columns
    # SMA-100 should be populated once enough history exists.
    assert out["sma_100"].notna().iloc[-1]
