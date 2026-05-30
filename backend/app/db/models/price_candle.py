from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PriceCandle(Base):
    """A single OHLCV bar for a ticker at a given interval and timestamp.

    Composite primary key (ticker, interval, timestamp): there is exactly one
    candle per ticker/interval/time. This also gives us the index we need for
    range scans like "last 1y of daily candles for AAPL".
    """

    __tablename__ = "price_candles"

    ticker: Mapped[str] = mapped_column(
        String(20), ForeignKey("stocks.ticker", ondelete="CASCADE"), primary_key=True
    )
    interval: Mapped[str] = mapped_column(String(10), primary_key=True)  # 5m, 30m, 1d, 1wk
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)

    open: Mapped[float] = mapped_column(Float)
    high: Mapped[float] = mapped_column(Float)
    low: Mapped[float] = mapped_column(Float)
    close: Mapped[float] = mapped_column(Float)
    adj_close: Mapped[float | None] = mapped_column(Float)
    volume: Mapped[int | None] = mapped_column(BigInteger)
