from fastapi import APIRouter, Depends, HTTPException, Query
from redis import Redis
from sqlalchemy.orm import Session

from app.cache.redis_client import get_redis
from app.db.session import get_db
from app.ml.features import HORIZON_DAYS
from app.ml.registry import NoModelError
from app.schemas.prediction import PredictionHistoryItem, PredictionOut
from app.services import prediction_service
from app.services.market_data.base import InvalidTickerError, MarketDataProvider, ProviderError
from app.services.market_data.registry import get_provider

router = APIRouter(prefix="/predictions", tags=["predictions"])

_VALID_HORIZONS = list(HORIZON_DAYS)


@router.post("/{ticker}", response_model=PredictionOut)
def create_prediction(
    ticker: str,
    horizon: str = Query("7d", description=f"One of: {', '.join(_VALID_HORIZONS)}"),
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis),
    provider: MarketDataProvider = Depends(get_provider),
) -> dict:
    if horizon not in _VALID_HORIZONS:
        raise HTTPException(
            status_code=422, detail=f"Invalid horizon. Use one of: {', '.join(_VALID_HORIZONS)}"
        )
    try:
        return prediction_service.predict(db, redis, provider, ticker, horizon)
    except NoModelError:
        raise HTTPException(
            status_code=503,
            detail="No trained model available yet. Run scripts/train_baseline.py first.",
        ) from None
    except InvalidTickerError:
        raise HTTPException(status_code=404, detail=f"Unknown ticker: {ticker}") from None
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=f"Data provider error: {exc}") from exc


@router.get("/{ticker}/history", response_model=list[PredictionHistoryItem])
def prediction_history(
    ticker: str,
    horizon: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[dict]:
    return prediction_service.get_history(db, ticker, horizon, limit)
