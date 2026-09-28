from fastapi import APIRouter, Depends, HTTPException, Query
from redis import Redis
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.errors import provider_error
from app.cache.redis_client import get_redis
from app.core.config import get_settings
from app.core.rate_limit import rate_limit
from app.db.session import get_db
from app.ml.features import HORIZON_DAYS
from app.ml.registry import NoModelError
from app.schemas.prediction import PredictionHistoryItem, PredictionOut
from app.services import prediction_service
from app.services.market_data.base import InvalidTickerError, MarketDataProvider, ProviderError
from app.services.market_data.registry import get_provider

# Every call here runs model inference and appends a predictions row, so leaving
# it open was both a compute-abuse and an unbounded-write vector.
_settings = get_settings()
_predict_limiter = rate_limit(
    "predict", _settings.predict_rate_limit, _settings.predict_rate_window_seconds
)

router = APIRouter(
    prefix="/predictions",
    tags=["predictions"],
    dependencies=[Depends(get_current_user), Depends(_predict_limiter)],
)

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
        raise provider_error(exc) from exc


@router.get("/{ticker}/history", response_model=list[PredictionHistoryItem])
def prediction_history(
    ticker: str,
    horizon: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[dict]:
    return prediction_service.get_history(db, ticker, horizon, limit)
