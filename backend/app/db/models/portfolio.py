import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

# Money and share counts are stored as exact decimals rather than floats. A
# ledger that drifts by fractions of a cent after a few hundred trades is the
# kind of bug a brokerage would never ship, even a paper one.
_MONEY = Numeric(18, 4)
_SHARES = Numeric(20, 6)


class Portfolio(Base):
    """A user's paper-trading account: one per user, seeded with starting cash.

    Positions and the trade ledger hang off this row, so moving a guest's
    portfolio to the account they sign in to is a single column update.
    """

    __tablename__ = "portfolios"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    cash: Mapped[Decimal] = mapped_column(_MONEY)
    starting_cash: Mapped[Decimal] = mapped_column(_MONEY)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    reset_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Position(Base):
    """An open holding. `avg_cost` is the volume-weighted entry price, which is
    what unrealized P&L is measured against."""

    __tablename__ = "positions"
    __table_args__ = (UniqueConstraint("portfolio_id", "ticker", name="uq_positions_ticker"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    portfolio_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("portfolios.id", ondelete="CASCADE"), index=True
    )
    ticker: Mapped[str] = mapped_column(String(20), ForeignKey("stocks.ticker", ondelete="CASCADE"))
    quantity: Mapped[Decimal] = mapped_column(_SHARES)
    avg_cost: Mapped[Decimal] = mapped_column(_MONEY)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Trade(Base):
    """One fill in the ledger. Append-only: the ledger is the source of truth
    that cash and positions can always be rebuilt from."""

    __tablename__ = "trades"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    portfolio_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("portfolios.id", ondelete="CASCADE"), index=True
    )
    ticker: Mapped[str] = mapped_column(String(20), index=True)
    side: Mapped[str] = mapped_column(String(4))  # buy / sell
    quantity: Mapped[Decimal] = mapped_column(_SHARES)
    price: Mapped[Decimal] = mapped_column(_MONEY)
    # Only sells realize anything; buys leave this null.
    realized_pnl: Mapped[Decimal | None] = mapped_column(_MONEY)
    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
