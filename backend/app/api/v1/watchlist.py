from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.watchlist import WatchlistItemOut
from app.services import watchlist_service
from app.services.market_data.base import InvalidTickerError

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


@router.get("", response_model=list[WatchlistItemOut])
def get_watchlist(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[dict]:
    return watchlist_service.list_watchlist(db, user.id)


@router.post("/{ticker}", response_model=list[WatchlistItemOut])
def add_to_watchlist(
    ticker: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[dict]:
    try:
        watchlist_service.add(db, user.id, ticker)
    except InvalidTickerError:
        raise HTTPException(status_code=422, detail=f"Invalid ticker: {ticker}") from None
    return watchlist_service.list_watchlist(db, user.id)


@router.delete("/{ticker}", response_model=list[WatchlistItemOut])
def remove_from_watchlist(
    ticker: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[dict]:
    watchlist_service.remove(db, user.id, ticker)
    return watchlist_service.list_watchlist(db, user.id)
