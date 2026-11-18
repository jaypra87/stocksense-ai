"""Paper trading: one cash account per user, fills at the live quote.

Everything money-shaped is a Decimal from the moment the quote is read until
the row is written; floats appear only in the dict handed to the response
schema. Orders are sized in shares or in money, and a sell is allowed to close
a position exactly even when the client rounds the share count on its way in.
"""

import logging
import uuid
from datetime import UTC, datetime
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal

from redis import Redis
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.portfolio import Portfolio, Position, Trade
from app.db.models.stock import Stock
from app.services import stock_service
from app.services.market_data.base import MarketDataProvider, ProviderError

logger = logging.getLogger(__name__)

STARTING_CASH = Decimal("100000")
# Smallest order the ledger accepts. Fractional shares are allowed, dust is not.
MIN_QUANTITY = Decimal("0.000001")

_CENTS = Decimal("0.0001")
_SHARES = Decimal("0.000001")

DISCLAIMER = (
    "Paper trading with simulated money. Fills use delayed quotes and ignore "
    "fees, slippage and market hours. Educational only, not financial advice."
)


class TradeError(Exception):
    """An order the account cannot honour. The message is safe to show."""


class InsufficientFundsError(TradeError):
    def __init__(self, cost: Decimal, cash: Decimal) -> None:
        super().__init__(f"Order costs {cost:,.2f} but only {cash:,.2f} cash is available")


class InsufficientSharesError(TradeError):
    def __init__(self, ticker: str, wanted: Decimal, held: Decimal) -> None:
        super().__init__(f"Cannot sell {wanted:f} {ticker}: holding {held:f}")


def get_or_create(db: Session, user_id: uuid.UUID) -> Portfolio:
    portfolio = db.execute(
        select(Portfolio).where(Portfolio.user_id == user_id)
    ).scalar_one_or_none()
    if portfolio is None:
        portfolio = Portfolio(user_id=user_id, cash=STARTING_CASH, starting_cash=STARTING_CASH)
        db.add(portfolio)
        db.commit()
        db.refresh(portfolio)
    return portfolio


def summary(db: Session, redis: Redis, provider: MarketDataProvider, user_id: uuid.UUID) -> dict:
    portfolio = get_or_create(db, user_id)
    rows = db.execute(
        select(Position, Stock.company_name, Stock.currency)
        .join(Stock, Stock.ticker == Position.ticker)
        .where(Position.portfolio_id == portfolio.id)
        .order_by(Position.opened_at)
    ).all()

    positions: list[dict] = []
    market_value = Decimal(0)
    cost_basis = Decimal(0)
    day_change = Decimal(0)
    for position, company_name, currency in rows:
        price, change, stale = _mark(redis, provider, position)
        value = (position.quantity * price).quantize(_CENTS)
        basis = (position.quantity * position.avg_cost).quantize(_CENTS)
        pnl = value - basis
        pos_day = (position.quantity * change).quantize(_CENTS) if change is not None else None
        market_value += value
        cost_basis += basis
        if pos_day is not None:
            day_change += pos_day
        positions.append(
            {
                "ticker": position.ticker,
                "company_name": company_name,
                "currency": currency,
                "quantity": float(position.quantity),
                "avg_cost": float(position.avg_cost),
                "price": float(price),
                "price_stale": stale,
                "cost_basis": float(basis),
                "market_value": float(value),
                "unrealized_pnl": float(pnl),
                "unrealized_pnl_pct": _pct(pnl, basis),
                "day_change": float(pos_day) if pos_day is not None else None,
                "day_change_pct": (_pct(pos_day, value - pos_day) if pos_day is not None else None),
                "weight": 0.0,
            }
        )

    equity = portfolio.cash + market_value
    for item in positions:
        item["weight"] = _pct(Decimal(str(item["market_value"])), equity)

    realized_pnl = db.execute(
        select(func.sum(Trade.realized_pnl)).where(Trade.portfolio_id == portfolio.id)
    ).scalar_one() or Decimal(0)
    total_return = equity - portfolio.starting_cash

    return {
        "cash": float(portfolio.cash),
        "starting_cash": float(portfolio.starting_cash),
        "equity": float(equity),
        "market_value": float(market_value),
        "unrealized_pnl": float(market_value - cost_basis),
        "realized_pnl": float(realized_pnl),
        "total_return": float(total_return),
        "total_return_pct": _pct(total_return, portfolio.starting_cash),
        "day_change": float(day_change),
        "day_change_pct": _pct(day_change, equity - day_change),
        "positions": positions,
        "as_of": datetime.now(UTC).isoformat(),
        "reset_at": portfolio.reset_at.isoformat() if portfolio.reset_at else None,
        "disclaimer": DISCLAIMER,
    }


def trade(
    db: Session,
    redis: Redis,
    provider: MarketDataProvider,
    user_id: uuid.UUID,
    raw_ticker: str,
    side: str,
    quantity: Decimal | None = None,
    amount: Decimal | None = None,
) -> dict:
    """Fill an order at the current quote and record it in the ledger."""
    quote = stock_service.get_quote(redis, provider, raw_ticker)
    ticker = stock_service.ensure_stock(db, quote["ticker"])
    price = Decimal(str(quote["price"])).quantize(_CENTS)

    if quantity is None:
        assert amount is not None
        quantity = (amount / price).quantize(_SHARES, rounding=ROUND_DOWN)
    quantity = quantity.quantize(_SHARES)
    if quantity < MIN_QUANTITY:
        raise TradeError("Order is too small to fill")

    # The row lock serialises two orders from the same account, so a double
    # submit cannot spend the same cash twice.
    portfolio = get_or_create(db, user_id)
    portfolio = db.execute(
        select(Portfolio).where(Portfolio.id == portfolio.id).with_for_update()
    ).scalar_one()
    position = db.execute(
        select(Position).where(Position.portfolio_id == portfolio.id, Position.ticker == ticker)
    ).scalar_one_or_none()

    realized: Decimal | None = None
    if side == "buy":
        _buy(portfolio, position, ticker, quantity, price, db)
    else:
        quantity, realized = _sell(portfolio, position, ticker, quantity, price, db)

    fill = Trade(
        portfolio_id=portfolio.id,
        ticker=ticker,
        side=side,
        quantity=quantity,
        price=price,
        realized_pnl=realized,
    )
    db.add(fill)
    db.commit()
    db.refresh(fill)
    return _trade_dict(fill)


def _buy(
    portfolio: Portfolio,
    position: Position | None,
    ticker: str,
    quantity: Decimal,
    price: Decimal,
    db: Session,
) -> None:
    cost = (quantity * price).quantize(_CENTS)
    if cost > portfolio.cash:
        raise InsufficientFundsError(cost, portfolio.cash)
    portfolio.cash -= cost
    if position is None:
        db.add(
            Position(portfolio_id=portfolio.id, ticker=ticker, quantity=quantity, avg_cost=price)
        )
        return
    held = position.quantity
    position.avg_cost = ((held * position.avg_cost + cost) / (held + quantity)).quantize(
        _CENTS, rounding=ROUND_HALF_UP
    )
    position.quantity = held + quantity


def _sell(
    portfolio: Portfolio,
    position: Position | None,
    ticker: str,
    quantity: Decimal,
    price: Decimal,
    db: Session,
) -> tuple[Decimal, Decimal]:
    held = position.quantity if position is not None else Decimal(0)
    # "Sell everything" arrives as a share count the client rounded to six
    # places; treat anything within one unit of the holding as the whole lot.
    if abs(quantity - held) <= _SHARES:
        quantity = held
    if position is None or quantity > held:
        raise InsufficientSharesError(ticker, quantity, held)

    proceeds = (quantity * price).quantize(_CENTS)
    realized = (proceeds - quantity * position.avg_cost).quantize(_CENTS)
    portfolio.cash += proceeds
    position.quantity = held - quantity
    if position.quantity == 0:
        db.delete(position)
    return quantity, realized


def list_trades(db: Session, user_id: uuid.UUID, limit: int = 50) -> list[dict]:
    portfolio = get_or_create(db, user_id)
    rows = (
        db.execute(
            select(Trade)
            .where(Trade.portfolio_id == portfolio.id)
            .order_by(Trade.executed_at.desc())
            .limit(limit)
        )
        .scalars()
        .all()
    )
    return [_trade_dict(t) for t in rows]


def reset(db: Session, user_id: uuid.UUID) -> None:
    """Wipe positions and the ledger and restore the starting balance."""
    portfolio = get_or_create(db, user_id)
    for model in (Position, Trade):
        for row in db.execute(select(model).where(model.portfolio_id == portfolio.id)).scalars():
            db.delete(row)
    portfolio.cash = portfolio.starting_cash
    portfolio.reset_at = datetime.now(UTC)
    db.commit()


def _mark(
    redis: Redis, provider: MarketDataProvider, position: Position
) -> tuple[Decimal, Decimal | None, bool]:
    """Current price and day change for a position. A dead quote feed marks
    the position at cost rather than hiding it from the page."""
    try:
        quote = stock_service.get_quote(redis, provider, position.ticker)
    except ProviderError as exc:
        logger.warning("quote unavailable for %s: %s", position.ticker, exc)
        return position.avg_cost, None, True
    price = Decimal(str(quote["price"])).quantize(_CENTS)
    change = quote.get("change")
    return price, (Decimal(str(change)) if change is not None else None), False


def _pct(part: Decimal, whole: Decimal) -> float:
    if whole == 0:
        return 0.0
    return float((part / whole * 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _trade_dict(t: Trade) -> dict:
    return {
        "id": str(t.id),
        "ticker": t.ticker,
        "side": t.side,
        "quantity": float(t.quantity),
        "price": float(t.price),
        "total": float((t.quantity * t.price).quantize(_CENTS)),
        "realized_pnl": float(t.realized_pnl) if t.realized_pnl is not None else None,
        "executed_at": t.executed_at.isoformat() if t.executed_at else None,
    }
