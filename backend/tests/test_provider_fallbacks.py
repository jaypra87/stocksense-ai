"""Provider degradation when Yahoo's authenticated endpoints are refused.

On a cloud host the public chart endpoint (`Ticker.history`) keeps working while
the crumb/cookie-gated ones (`fast_info`, `info`, `news`, `Search`) get refused.
These tests pin the resulting behaviour: derive what we can from candles, and
only call a ticker invalid when even the chart endpoint has nothing.

No network — the provider's own candle fetch is stubbed.
"""

from datetime import UTC, datetime, timedelta

import pytest

from app.services.market_data.base import CandleDTO, InvalidTickerError
from app.services.market_data.symbols import search_offline
from app.services.market_data.yfinance_provider import YFinanceProvider


def _candles(closes: list[float]) -> list[CandleDTO]:
    start = datetime(2026, 1, 2, tzinfo=UTC)
    return [
        CandleDTO(
            timestamp=start + timedelta(days=i),
            open=c - 1,
            high=c + 2,
            low=c - 3,
            close=c,
            adj_close=c,
            volume=1_000 + i,
        )
        for i, c in enumerate(closes)
    ]


@pytest.fixture
def provider(monkeypatch: pytest.MonkeyPatch) -> YFinanceProvider:
    """A provider whose crumb-gated calls all fail, but whose charts work."""
    p = YFinanceProvider()
    monkeypatch.setattr(
        p, "get_candles", lambda *a, **k: _candles([100.0, 104.0, 102.0])
    )
    return p


def test_quote_falls_back_to_the_latest_candle(provider: YFinanceProvider) -> None:
    quote = provider._quote_from_candles("NVDA")

    assert quote.ticker == "NVDA"
    assert quote.price == 102.0
    assert quote.previous_close == 104.0
    assert quote.change == pytest.approx(-2.0)
    assert quote.change_percent == pytest.approx(-2.0 / 104.0 * 100)


def test_fallback_quote_is_stamped_with_the_bar_time_not_now(
    provider: YFinanceProvider,
) -> None:
    """A close from last session must not be presented as a live price."""
    quote = provider._quote_from_candles("NVDA")
    assert quote.as_of == datetime(2026, 1, 4, tzinfo=UTC)
    assert quote.as_of < datetime.now(UTC)


def test_fallback_quote_leaves_underivable_fields_empty(
    provider: YFinanceProvider,
) -> None:
    """Better an absent market cap than an invented one."""
    quote = provider._quote_from_candles("NVDA")
    assert quote.market_cap is None
    assert quote.currency is None
    assert quote.exchange is None
    # 52-week range *is* derivable from the candle window.
    assert quote.fifty_two_week_high == 106.0
    assert quote.fifty_two_week_low == 97.0


def test_single_candle_yields_a_price_without_a_change(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    p = YFinanceProvider()
    monkeypatch.setattr(p, "get_candles", lambda *a, **k: _candles([100.0]))
    quote = p._quote_from_candles("NEW")
    assert quote.price == 100.0
    assert quote.previous_close is None
    assert quote.change is None


def test_no_candles_means_the_ticker_really_is_invalid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    p = YFinanceProvider()
    monkeypatch.setattr(p, "get_candles", lambda *a, **k: [])
    with pytest.raises(InvalidTickerError):
        p._quote_from_candles("NOTAREALTICKER")


def test_metadata_degrades_to_a_bare_profile_when_info_is_blocked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    p = YFinanceProvider()
    monkeypatch.setattr(p, "get_candles", lambda *a, **k: _candles([100.0, 101.0]))

    class _Blocked:
        def __init__(self, *a: object, **k: object) -> None: ...

        @property
        def info(self) -> dict:
            raise RuntimeError("401 Unauthorized (crumb)")

    monkeypatch.setattr("app.services.market_data.yfinance_provider.yf.Ticker", _Blocked)

    meta = p.get_metadata("NVDA")
    assert meta.ticker == "NVDA"
    assert meta.company_name is None  # unknown, not fabricated


def test_metadata_still_raises_for_a_symbol_with_no_candles(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    p = YFinanceProvider()
    monkeypatch.setattr(p, "get_candles", lambda *a, **k: [])

    class _Blocked:
        def __init__(self, *a: object, **k: object) -> None: ...

        @property
        def info(self) -> dict:
            raise RuntimeError("401 Unauthorized (crumb)")

    monkeypatch.setattr("app.services.market_data.yfinance_provider.yf.Ticker", _Blocked)

    with pytest.raises(InvalidTickerError):
        p.get_metadata("NOTAREALTICKER")


# --- offline search index ----------------------------------------------------


def test_offline_search_resolves_a_company_name_to_its_ticker() -> None:
    assert "GOOGL" in [r["symbol"] for r in search_offline("google")]


def test_offline_search_ranks_an_exact_symbol_first() -> None:
    assert search_offline("v")[0]["symbol"] == "V"


def test_offline_search_is_case_insensitive_and_bounded() -> None:
    assert search_offline("NVDA") == search_offline("nvda")
    assert len(search_offline("a", limit=3)) <= 3


def test_offline_search_returns_nothing_for_an_unknown_name() -> None:
    assert search_offline("zzzz-not-a-company") == []


def test_search_uses_the_offline_index_when_upstream_is_blocked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _blocked(*a: object, **k: object) -> None:
        raise RuntimeError("429 Too Many Requests")

    monkeypatch.setattr("app.services.market_data.yfinance_provider.yf.Search", _blocked)

    results = YFinanceProvider().search("google", limit=5)
    assert "GOOGL" in [r.symbol for r in results]
