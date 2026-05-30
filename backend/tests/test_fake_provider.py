from app.services.market_data.fake_provider import FakeProvider


def test_search_matches_known_tickers() -> None:
    results = FakeProvider().search("AAPL")
    assert any(r.symbol == "AAPL" for r in results)


def test_candles_are_deterministic() -> None:
    a = FakeProvider().get_candles("NVDA", "1y", "1d")
    b = FakeProvider().get_candles("NVDA", "1y", "1d")
    assert len(a) == len(b) == 252
    assert [c.close for c in a] == [c.close for c in b]


def test_candles_have_valid_ohlc() -> None:
    for c in FakeProvider().get_candles("TSLA", "1m", "1d"):
        assert c.high >= c.open and c.high >= c.close
        assert c.low <= c.open and c.low <= c.close
        assert c.volume and c.volume > 0


def test_candle_timestamps_are_stable_across_calls() -> None:
    # Regression: timestamps must not drift between calls, or the DB upsert
    # key never collides and we insert duplicate rows instead of updating.
    a = FakeProvider().get_candles("AAPL", "1m", "1d")
    b = FakeProvider().get_candles("AAPL", "1m", "1d")
    assert [c.timestamp for c in a] == [c.timestamp for c in b]


def test_quote_derives_change_from_candles() -> None:
    q = FakeProvider().get_quote("MSFT")
    assert q.ticker == "MSFT"
    assert q.price > 0
    assert q.change_percent is not None


def test_metadata_known_vs_unknown() -> None:
    known = FakeProvider().get_metadata("AAPL")
    assert known.company_name == "Apple Inc."
    unknown = FakeProvider().get_metadata("ZZZZ")
    assert unknown.ticker == "ZZZZ"
