from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TechnicalIndicator(Base):
    """Computed indicators for a ticker at a daily timestamp.

    Implicitly daily (no interval column) — indicators are computed on daily
    candles. Composite PK (ticker, timestamp) gives one row per day.
    """

    __tablename__ = "technical_indicators"

    ticker: Mapped[str] = mapped_column(
        String(20), ForeignKey("stocks.ticker", ondelete="CASCADE"), primary_key=True
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)

    sma_7: Mapped[float | None] = mapped_column(Float)
    sma_30: Mapped[float | None] = mapped_column(Float)
    sma_100: Mapped[float | None] = mapped_column(Float)
    ema_20: Mapped[float | None] = mapped_column(Float)
    rsi_14: Mapped[float | None] = mapped_column(Float)
    macd: Mapped[float | None] = mapped_column(Float)
    macd_signal: Mapped[float | None] = mapped_column(Float)
    macd_hist: Mapped[float | None] = mapped_column(Float)
    bollinger_mid: Mapped[float | None] = mapped_column(Float)
    bollinger_upper: Mapped[float | None] = mapped_column(Float)
    bollinger_lower: Mapped[float | None] = mapped_column(Float)
    volatility_30: Mapped[float | None] = mapped_column(Float)
    drawdown: Mapped[float | None] = mapped_column(Float)
    daily_return: Mapped[float | None] = mapped_column(Float)
    relative_volume: Mapped[float | None] = mapped_column(Float)
    volume_spike: Mapped[bool | None] = mapped_column(Boolean)
