import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Prediction(Base):
    """A single stored forecast. Append-only — we keep prediction history so we
    can later backtest our own past predictions (Phase 9)."""

    __tablename__ = "predictions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    ticker: Mapped[str] = mapped_column(
        String(20), ForeignKey("stocks.ticker", ondelete="CASCADE"), index=True
    )
    horizon: Mapped[str] = mapped_column(String(10), index=True)

    trend: Mapped[str] = mapped_column(String(10))  # bullish / bearish / neutral
    confidence: Mapped[float] = mapped_column(Float)

    expected_return_low: Mapped[float | None] = mapped_column(Float)
    expected_return_high: Mapped[float | None] = mapped_column(Float)
    expected_low: Mapped[float | None] = mapped_column(Float)
    expected_high: Mapped[float | None] = mapped_column(Float)

    risk_score: Mapped[float | None] = mapped_column(Float)  # filled in Phase 6

    model_version: Mapped[str] = mapped_column(String(50))
    explanation: Mapped[dict] = mapped_column(JSONB, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
