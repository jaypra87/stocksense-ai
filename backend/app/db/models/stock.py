from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Stock(Base):
    """Master record for a tradable instrument. One row per ticker."""

    __tablename__ = "stocks"

    # Ticker is the natural primary key (e.g. "AAPL", "VFV.TO", "BRK-B").
    ticker: Mapped[str] = mapped_column(String(20), primary_key=True)

    exchange: Mapped[str | None] = mapped_column(String(50))
    company_name: Mapped[str | None] = mapped_column(String(255))
    sector: Mapped[str | None] = mapped_column(String(100))
    currency: Mapped[str | None] = mapped_column(String(10))

    # Anything provider-specific we don't model as columns (industry, website, summary...).
    # Named *_json because `metadata` is reserved by SQLAlchemy's Declarative base.
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
