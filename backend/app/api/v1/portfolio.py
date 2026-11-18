from fastapi import APIRouter, Depends, HTTPException, Query
from redis import Redis
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.errors import provider_error
from app.cache.redis_client import get_redis
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.portfolio import PortfolioOut, TradeCreate, TradeOut
from app.services import portfolio_service
from app.services.market_data.base import InvalidTickerError, MarketDataProvider, ProviderError
from app.services.market_data.registry import get_provider
from app.services.portfolio_service import TradeError

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("", response_model=PortfolioOut)
def get_portfolio(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis),
    provider: MarketDataProvider = Depends(get_provider),
) -> dict:
    return portfolio_service.summary(db, redis, provider, user.id)


@router.post("/trades", response_model=TradeOut, status_code=201)
def place_trade(
    body: TradeCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis),
    provider: MarketDataProvider = Depends(get_provider),
) -> dict:
    try:
        return portfolio_service.trade(
            db, redis, provider, user.id, body.ticker, body.side, body.quantity, body.amount
        )
    except InvalidTickerError:
        raise HTTPException(status_code=422, detail=f"Invalid ticker: {body.ticker}") from None
    except TradeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    except ProviderError as exc:
        raise provider_error(exc) from None


@router.get("/trades", response_model=list[TradeOut])
def list_trades(
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    return portfolio_service.list_trades(db, user.id, limit)


@router.post("/reset", response_model=PortfolioOut)
def reset_portfolio(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis),
    provider: MarketDataProvider = Depends(get_provider),
) -> dict:
    portfolio_service.reset(db, user.id)
    return portfolio_service.summary(db, redis, provider, user.id)
