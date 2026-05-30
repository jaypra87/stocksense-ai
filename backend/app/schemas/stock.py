"""API response shapes for the /stocks endpoints.

These are the public contract the frontend consumes. They're separate from the
provider DTOs on purpose: the wire format the app exposes shouldn't be coupled
to whatever a vendor happens to return.
"""

from datetime import datetime

from pydantic import BaseModel


class SearchResultOut(BaseModel):
    symbol: str
    name: str | None = None
    exchange: str | None = None
    type: str | None = None


class StockOut(BaseModel):
    ticker: str
    company_name: str | None = None
    exchange: str | None = None
    sector: str | None = None
    currency: str | None = None
    metadata: dict = {}
    updated_at: datetime | None = None


class QuoteOut(BaseModel):
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


class CandleOut(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    adj_close: float | None = None
    volume: int | None = None


class HistoryOut(BaseModel):
    ticker: str
    range: str
    interval: str
    candles: list[CandleOut]
