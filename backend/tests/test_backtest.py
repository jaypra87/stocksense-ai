import pandas as pd
import pytest

from app.ml.backtest import NotEnoughDataError, run_walk_forward
from app.ml.features import candles_to_frame
from app.services.indicators import compute_indicators
from app.services.market_data.fake_provider import FakeProvider


def _frame(period: str = "5y") -> pd.DataFrame:
    candles = FakeProvider().get_candles("AAPL", period, "1d")
    return compute_indicators(candles_to_frame(candles))


def test_walk_forward_returns_metrics_and_chart() -> None:
    result = run_walk_forward(_frame(), "7d")
    m = result["metrics"]
    assert m["n_predictions"] > 0
    assert 0 <= m["directional_accuracy"] <= 100
    assert 0 <= m["baseline_accuracy"] <= 100
    assert m["mae"] >= 0 and m["rmse"] >= 0
    assert "beats_baseline" in m
    # Chart series line up with the number of predictions.
    assert len(result["chart_data"]["equity"]) == m["n_predictions"]
    assert len(result["chart_data"]["returns"]) == m["n_predictions"]


def test_walk_forward_dates_are_ordered() -> None:
    result = run_walk_forward(_frame(), "30d")
    assert result["start_date"] <= result["end_date"]


def test_not_enough_data_raises() -> None:
    with pytest.raises(NotEnoughDataError):
        run_walk_forward(_frame("1mo"), "30d")
