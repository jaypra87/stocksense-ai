import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.ml.backtest import NotEnoughDataError
from app.ml.features import HORIZON_DAYS
from app.schemas.backtest import BacktestOut, BacktestSummary
from app.services import backtest_service
from app.services.market_data.base import InvalidTickerError, MarketDataProvider, ProviderError
from app.services.market_data.registry import get_provider

router = APIRouter(prefix="/backtests", tags=["backtests"])

_VALID_HORIZONS = list(HORIZON_DAYS)


@router.post("/{ticker}", response_model=BacktestOut)
def run_backtest(
    ticker: str,
    horizon: str = Query("7d", description=f"One of: {', '.join(_VALID_HORIZONS)}"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    provider: MarketDataProvider = Depends(get_provider),
) -> dict:
    if horizon not in _VALID_HORIZONS:
        raise HTTPException(
            status_code=422, detail=f"Invalid horizon. Use one of: {', '.join(_VALID_HORIZONS)}"
        )
    try:
        return backtest_service.run_backtest(db, provider, user.id, ticker, horizon)
    except NotEnoughDataError as exc:
        raise HTTPException(status_code=422, detail=f"Not enough history: {exc}") from None
    except InvalidTickerError:
        raise HTTPException(status_code=404, detail=f"Unknown ticker: {ticker}") from None
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=f"Data provider error: {exc}") from exc


@router.get("", response_model=list[BacktestSummary])
def list_backtests(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[dict]:
    return backtest_service.list_backtests(db, user.id)


@router.get("/{backtest_id}", response_model=BacktestOut)
def get_backtest(
    backtest_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    result = backtest_service.get_backtest(db, user.id, backtest_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Backtest not found")
    return result
