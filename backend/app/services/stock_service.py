"""Orchestration layer for stock data.

Pattern in every function: validate input -> check cache / DB -> call provider
only when needed -> normalize -> persist -> return. Routers call these functions
and stay thin. This module is the one place that knows about cache + DB + provider
all at once.
"""

import re

from redis import Redis
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.cache.cache import cached_json
from app.cache.keys import (
    TTL_METADATA,
    TTL_QUOTE,
    TTL_SEARCH,
    metadata_key,
    quote_key,
    search_key,
)
from app.db.models.price_candle import PriceCandle
from app.db.models.stock import Stock
from app.services.market_data.base import (
    InvalidTickerError,
    MarketDataProvider,
)

# Allows AAPL, BRK-B, VFV.TO — letters/digits with an optional exchange/class suffix.
_TICKER_RE = re.compile(r"^[A-Z0-9]{1,10}([.\-][A-Z0-9]{1,6})?$")

# Maps the public `range` param to a yfinance (period, default interval) pair.
_RANGE_MAP: dict[str, tuple[str, str]] = {
    "1d": ("1d", "5m"),
    "5d": ("5d", "30m"),
    "1m": ("1mo", "1d"),
    "6m": ("6mo", "1d"),
    "ytd": ("ytd", "1d"),
    "1y": ("1y", "1d"),
    "5y": ("5y", "1wk"),
}

def normalize_ticker(raw: str) -> str:
    """Uppercase, strip, and validate the ticker format. Raises InvalidTickerError."""
    ticker = raw.strip().upper()
    if not _TICKER_RE.match(ticker):
        raise InvalidTickerError(raw)
    return ticker


def resolve_range(range_: str, interval: str | None) -> tuple[str, str]:
    """Turn a public range (+ optional interval override) into (period, interval)."""
    if range_ not in _RANGE_MAP:
        raise ValueError(f"unsupported range: {range_}")
    period, default_interval = _RANGE_MAP[range_]
    return period, interval or default_interval


def search(redis: Redis, provider: MarketDataProvider, query: str, limit: int = 10) -> list[dict]:
    def produce() -> list[dict]:
        return [r.model_dump() for r in provider.search(query, limit)]

    return cached_json(redis, search_key(query, limit), TTL_SEARCH, produce)


def get_quote(redis: Redis, provider: MarketDataProvider, raw_ticker: str) -> dict:
    ticker = normalize_ticker(raw_ticker)

    def produce() -> dict:
        return provider.get_quote(ticker).model_dump(mode="json")

    return cached_json(redis, quote_key(ticker), TTL_QUOTE, produce)


def get_stock(
    db: Session, redis: Redis, provider: MarketDataProvider, raw_ticker: str
) -> dict:
    """Return company metadata, fetching + persisting on a cache miss."""
    ticker = normalize_ticker(raw_ticker)

    def produce() -> dict:
        meta = provider.get_metadata(ticker)
        _upsert_stock(
            db,
            ticker=meta.ticker,
            company_name=meta.company_name,
            exchange=meta.exchange,
            sector=meta.sector,
            currency=meta.currency,
            metadata_json=meta.extra,
        )
        return {
            "ticker": meta.ticker,
            "company_name": meta.company_name,
            "exchange": meta.exchange,
            "sector": meta.sector,
            "currency": meta.currency,
            "metadata": meta.extra,
        }

    return cached_json(redis, metadata_key(ticker), TTL_METADATA, produce)


def fetch_and_store_candles(
    db: Session,
    provider: MarketDataProvider,
    ticker: str,
    period: str,
    interval: str,
) -> list:
    """Fetch candles from the provider and persist them. `ticker` must be normalized.

    Shared by get_history and the indicator service so the fetch+persist logic
    lives in exactly one place.
    """
    candles = provider.get_candles(ticker, period, interval)
    if not candles:
        raise InvalidTickerError(ticker)

    # The FK on price_candles requires the parent stock row to exist first.
    _ensure_stock_row(db, ticker)
    _upsert_candles(db, ticker, interval, candles)
    return candles


def get_history(
    db: Session,
    provider: MarketDataProvider,
    raw_ticker: str,
    range_: str = "1y",
    interval: str | None = None,
) -> dict:
    """Fetch candles for the requested window and return them (also persisted).

    Returns the freshly-fetched candles directly rather than re-reading the DB.
    Re-reading the accumulated table can mix candles from different providers or
    vintages (e.g. synthetic vs yfinance, stored at different timestamps), which
    renders as a spiky, zig-zagging chart. The current fetch is the clean,
    single-source view for the requested period.
    """
    ticker = normalize_ticker(raw_ticker)
    period, resolved_interval = resolve_range(range_, interval)

    candles = fetch_and_store_candles(db, provider, ticker, period, resolved_interval)
    candles = sorted(candles, key=lambda c: c.timestamp)

    return {
        "ticker": ticker,
        "range": range_,
        "interval": resolved_interval,
        "candles": [
            {
                "timestamp": c.timestamp,
                "open": c.open,
                "high": c.high,
                "low": c.low,
                "close": c.close,
                "adj_close": c.adj_close,
                "volume": c.volume,
            }
            for c in candles
        ],
    }


def ensure_stock(db: Session, raw_ticker: str) -> str:
    """Public: validate ticker format and ensure a stocks row exists. Returns
    the normalized ticker. Used by the watchlist service."""
    ticker = normalize_ticker(raw_ticker)
    _ensure_stock_row(db, ticker)
    return ticker


# --- DB helpers (Postgres upserts) ---


def _ensure_stock_row(db: Session, ticker: str) -> None:
    stmt = pg_insert(Stock).values(ticker=ticker).on_conflict_do_nothing(index_elements=["ticker"])
    db.execute(stmt)
    db.commit()


def _upsert_stock(db: Session, **values: object) -> None:
    stmt = pg_insert(Stock).values(**values)
    update_cols = {k: getattr(stmt.excluded, k) for k in values if k != "ticker"}
    stmt = stmt.on_conflict_do_update(index_elements=["ticker"], set_=update_cols)
    db.execute(stmt)
    db.commit()


def _upsert_candles(db: Session, ticker: str, interval: str, candles: list) -> None:
    rows = [
        {
            "ticker": ticker,
            "interval": interval,
            "timestamp": c.timestamp,
            "open": c.open,
            "high": c.high,
            "low": c.low,
            "close": c.close,
            "adj_close": c.adj_close,
            "volume": c.volume,
        }
        for c in candles
    ]
    stmt = pg_insert(PriceCandle).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=["ticker", "interval", "timestamp"],
        set_={
            "open": stmt.excluded.open,
            "high": stmt.excluded.high,
            "low": stmt.excluded.low,
            "close": stmt.excluded.close,
            "adj_close": stmt.excluded.adj_close,
            "volume": stmt.excluded.volume,
        },
    )
    db.execute(stmt)
    db.commit()
