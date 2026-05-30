import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SentimentSnapshot(Base):
    """A point-in-time news-sentiment assessment for a ticker (append-only)."""

    __tablename__ = "sentiment_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    ticker: Mapped[str] = mapped_column(
        String(20), ForeignKey("stocks.ticker", ondelete="CASCADE"), index=True
    )
    sentiment_label: Mapped[str] = mapped_column(String(20))
    sentiment_score: Mapped[float] = mapped_column(Float)
    headline_count: Mapped[int] = mapped_column(Integer)
    summary: Mapped[str] = mapped_column(String(1000))
    source_json: Mapped[dict] = mapped_column(JSONB, default=dict)  # items + counts
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
