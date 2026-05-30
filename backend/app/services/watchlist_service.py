"""Watchlist CRUD, scoped to a user."""

import uuid

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.db.models.stock import Stock
from app.db.models.watchlist import WatchlistItem
from app.services import stock_service


def list_watchlist(db: Session, user_id: uuid.UUID) -> list[dict]:
    rows = db.execute(
        select(WatchlistItem, Stock.company_name)
        .join(Stock, Stock.ticker == WatchlistItem.ticker, isouter=True)
        .where(WatchlistItem.user_id == user_id)
        .order_by(WatchlistItem.created_at.desc())
    ).all()
    return [
        {
            "ticker": item.ticker,
            "company_name": company_name,
            "created_at": item.created_at.isoformat() if item.created_at else None,
        }
        for item, company_name in rows
    ]


def add(db: Session, user_id: uuid.UUID, raw_ticker: str) -> str:
    ticker = stock_service.ensure_stock(db, raw_ticker)  # validates + ensures FK parent
    stmt = (
        pg_insert(WatchlistItem)
        .values(user_id=user_id, ticker=ticker)
        .on_conflict_do_nothing(index_elements=["user_id", "ticker"])
    )
    db.execute(stmt)
    db.commit()
    return ticker


def remove(db: Session, user_id: uuid.UUID, raw_ticker: str) -> None:
    ticker = stock_service.normalize_ticker(raw_ticker)
    item = db.get(WatchlistItem, (user_id, ticker))
    if item is not None:
        db.delete(item)
        db.commit()
