import numpy as np
import pandas as pd

from app.ml.features import (
    FEATURE_COLS,
    build_feature_frame,
    candles_to_frame,
    make_training_matrix,
)
from app.services.indicators import compute_indicators
from app.services.market_data.fake_provider import FakeProvider


def _indicator_frame(ticker: str = "AAPL", period: str = "5y") -> pd.DataFrame:
    candles = FakeProvider().get_candles(ticker, period, "1d")
    return compute_indicators(candles_to_frame(candles))


def test_feature_frame_has_all_columns() -> None:
    f = build_feature_frame(_indicator_frame())
    for col in FEATURE_COLS:
        assert col in f.columns


def test_training_matrix_has_no_nans_and_aligned_lengths() -> None:
    X, yc, yr = make_training_matrix(_indicator_frame(), "7d")
    assert len(X) == len(yc) == len(yr)
    assert not X.isna().any().any()
    assert set(yc.unique()) <= {"bullish", "bearish", "neutral"}


def test_no_lookahead_label_drops_horizon_tail() -> None:
    # The last `horizon` rows have no forward return, so they must be dropped.
    ind = _indicator_frame()
    X, _, _ = make_training_matrix(ind, "30d")
    # Last usable feature timestamp must be at least 30 rows before the end.
    assert X.index.max() <= ind.index[-31]


def test_label_threshold_logic() -> None:
    # Construct a tiny frame and check bucketization by hand.
    idx = pd.date_range("2024-01-01", periods=40, freq="D", tz="UTC")
    close = pd.Series(np.linspace(100, 130, 40), index=idx)  # steadily rising
    df = pd.DataFrame(
        {"open": close, "high": close + 1, "low": close - 1, "close": close, "volume": 1_000_000},
        index=idx,
    )
    ind = compute_indicators(df)
    _, yc, _ = make_training_matrix(ind, "1d")
    # A steadily rising series should never be labeled bearish.
    assert "bearish" not in set(yc.unique())
