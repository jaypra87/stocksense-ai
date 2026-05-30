"""The market-data provider contract.

Everything above this layer (services, routers) depends ONLY on this interface
and these DTOs — never on yfinance or any specific vendor. That is what lets us
swap yfinance (dev) for Polygon/Finnhub (prod) without touching the rest of the app.
"""

from abc import ABC, abstractmethod
from datetime import datetime

from pydantic import BaseModel

# --- Data Transfer Objects: the normalized shapes every provider must return ---


class SearchResultDTO(BaseModel):
    symbol: str
    name: str | None = None
    exchange: str | None = None
    type: str | None = None  # EQUITY, ETF, etc.


class QuoteDTO(BaseModel):
    ticker: str
    price: float
    previous_close: float | None = None
    change: float | None = None
    change_percent: float | None = None
    open: float | None = None
    day_high: float | None = None
    day_low: float | None = None
    volume: int | None = None
    market_cap: float | None = None
    fifty_two_week_high: float | None = None
    fifty_two_week_low: float | None = None
    currency: str | None = None
    exchange: str | None = None
    as_of: datetime


class CandleDTO(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    adj_close: float | None = None
    volume: int | None = None


class MetadataDTO(BaseModel):
    ticker: str
    company_name: str | None = None
    exchange: str | None = None
    sector: str | None = None
    currency: str | None = None
    extra: dict = {}


class NewsItemDTO(BaseModel):
    title: str
    publisher: str | None = None
    url: str | None = None
    published_at: datetime | None = None
    summary: str | None = None


# --- Errors the rest of the app catches and maps to HTTP responses ---


class ProviderError(Exception):
    """The upstream data source failed (network, rate limit, bad response)."""


class InvalidTickerError(Exception):
    """The ticker doesn't exist or isn't a valid symbol."""


# --- The interface every provider implements ---


class MarketDataProvider(ABC):
    name: str = "base"

    @abstractmethod
    def search(self, query: str, limit: int = 10) -> list[SearchResultDTO]:
        """Autocomplete-style ticker search."""

    @abstractmethod
    def get_quote(self, ticker: str) -> QuoteDTO:
        """Latest price snapshot. Raises InvalidTickerError / ProviderError."""

    @abstractmethod
    def get_candles(self, ticker: str, period: str, interval: str) -> list[CandleDTO]:
        """Historical OHLCV bars. `period`/`interval` use yfinance-style codes."""

    @abstractmethod
    def get_metadata(self, ticker: str) -> MetadataDTO:
        """Company/instrument metadata. Raises InvalidTickerError / ProviderError."""

    @abstractmethod
    def get_news(self, ticker: str, limit: int = 10) -> list[NewsItemDTO]:
        """Recent news headlines. Returns [] if none/unavailable (never raises)."""
