from datetime import UTC, datetime

import pytest

from app.services.market_data.base import InvalidTickerError
from app.services.stock_service import _range_cutoff, normalize_ticker, resolve_range


def test_range_cutoff_is_more_recent_for_shorter_ranges() -> None:
    # A 1-month window must start later than a 1-year window.
    assert _range_cutoff("1m") > _range_cutoff("6m") > _range_cutoff("1y") > _range_cutoff("5y")


def test_range_cutoff_ytd_is_jan_first() -> None:
    cutoff = _range_cutoff("ytd")
    assert cutoff.month == 1 and cutoff.day == 1
    assert cutoff.year == datetime.now(UTC).year


@pytest.mark.parametrize(
    "raw,expected",
    [("aapl", "AAPL"), ("  msft ", "MSFT"), ("vfv.to", "VFV.TO"), ("brk-b", "BRK-B")],
)
def test_normalize_ticker_accepts_valid(raw: str, expected: str) -> None:
    assert normalize_ticker(raw) == expected


@pytest.mark.parametrize("raw", ["", "!!!", "TOOLONGTICKER123", "a b"])
def test_normalize_ticker_rejects_invalid(raw: str) -> None:
    with pytest.raises(InvalidTickerError):
        normalize_ticker(raw)


def test_resolve_range_defaults_interval() -> None:
    assert resolve_range("1y", None) == ("1y", "1d")
    assert resolve_range("1d", None) == ("1d", "5m")


def test_resolve_range_interval_override() -> None:
    assert resolve_range("1y", "1wk") == ("1y", "1wk")


def test_resolve_range_rejects_unknown() -> None:
    with pytest.raises(ValueError):
        resolve_range("10y", None)
