from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

TradeSide = Literal["buy", "sell"]


class TradeCreate(BaseModel):
    """A paper order. Size it in shares (`quantity`) or in money (`amount`),
    never both: the fill price is whatever the live quote says, so one of
    them is always derived from the other."""

    model_config = ConfigDict(extra="forbid")

    ticker: str = Field(min_length=1, max_length=20)
    side: TradeSide
    quantity: Decimal | None = Field(default=None, gt=0, max_digits=20, decimal_places=6)
    amount: Decimal | None = Field(default=None, gt=0, max_digits=18, decimal_places=2)

    @model_validator(mode="after")
    def _one_size(self) -> "TradeCreate":
        if (self.quantity is None) == (self.amount is None):
            raise ValueError("Provide either quantity or amount")
        return self


class TradeOut(BaseModel):
    id: str
    ticker: str
    side: TradeSide
    quantity: float
    price: float
    total: float
    realized_pnl: float | None = None
    executed_at: str | None = None


class PositionOut(BaseModel):
    ticker: str
    company_name: str | None = None
    currency: str | None = None
    quantity: float
    avg_cost: float
    price: float
    # True when the quote feed failed and `price` fell back to the entry price.
    price_stale: bool = False
    cost_basis: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    day_change: float | None = None
    day_change_pct: float | None = None
    weight: float  # share of total equity, 0-100


class PortfolioOut(BaseModel):
    cash: float
    starting_cash: float
    equity: float
    market_value: float
    unrealized_pnl: float
    realized_pnl: float
    total_return: float
    total_return_pct: float
    day_change: float
    day_change_pct: float
    positions: list[PositionOut]
    as_of: str
    reset_at: str | None = None
    disclaimer: str
