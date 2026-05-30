from fastapi import APIRouter, Depends, HTTPException, Query
from redis import Redis
from sqlalchemy.orm import Session

from app.cache.redis_client import get_redis
from app.db.session import get_db
from app.schemas.indicator import IndicatorsOut
from app.schemas.risk import RiskOut
from app.schemas.sentiment import SentimentOut
from app.schemas.stock import HistoryOut, QuoteOut, SearchResultOut, StockOut
from app.services import indicator_service, risk_service, sentiment_service, stock_service
from app.services.market_data.base import (
    InvalidTickerError,
    MarketDataProvider,
    ProviderError,
)
from app.services.market_data.registry import get_provider

router = APIRouter(prefix="/stocks", tags=["stocks"])

_VALID_RANGES = ["1d", "5d", "1m", "6m", "ytd", "1y", "5y"]


@router.get("/search", response_model=list[SearchResultOut])
def search_stocks(
    q: str = Query(..., min_length=1, description="Search query (name or symbol)"),
    limit: int = Query(10, ge=1, le=25),
    redis: Redis = Depends(get_redis),
    provider: MarketDataProvider = Depends(get_provider),
) -> list[dict]:
    return stock_service.search(redis, provider, q, limit)


@router.get("/{ticker}", response_model=StockOut)
def get_stock(
    ticker: str,
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis),
    provider: MarketDataProvider = Depends(get_provider),
) -> dict:
    try:
        return stock_service.get_stock(db, redis, provider, ticker)
    except InvalidTickerError:
        raise HTTPException(status_code=404, detail=f"Unknown ticker: {ticker}") from None
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=f"Data provider error: {exc}") from exc


@router.get("/{ticker}/quote", response_model=QuoteOut)
def get_quote(
    ticker: str,
    redis: Redis = Depends(get_redis),
    provider: MarketDataProvider = Depends(get_provider),
) -> dict:
    try:
        return stock_service.get_quote(redis, provider, ticker)
    except InvalidTickerError:
        raise HTTPException(status_code=404, detail=f"Unknown ticker: {ticker}") from None
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=f"Data provider error: {exc}") from exc


@router.get("/{ticker}/history", response_model=HistoryOut)
def get_history(
    ticker: str,
    range: str = Query("1y", description=f"One of: {', '.join(_VALID_RANGES)}"),
    interval: str | None = Query(None, description="Optional override, e.g. 1d, 1wk, 5m"),
    db: Session = Depends(get_db),
    provider: MarketDataProvider = Depends(get_provider),
) -> dict:
    if range not in _VALID_RANGES:
        raise HTTPException(
            status_code=422, detail=f"Invalid range. Use one of: {', '.join(_VALID_RANGES)}"
        )
    try:
        return stock_service.get_history(db, provider, ticker, range, interval)
    except InvalidTickerError:
        raise HTTPException(status_code=404, detail=f"Unknown ticker: {ticker}") from None
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=f"Data provider error: {exc}") from exc


@router.get("/{ticker}/indicators", response_model=IndicatorsOut)
def get_indicators(
    ticker: str,
    range: str = Query("1y", description=f"One of: {', '.join(_VALID_RANGES)}"),
    db: Session = Depends(get_db),
    provider: MarketDataProvider = Depends(get_provider),
) -> dict:
    if range not in _VALID_RANGES:
        raise HTTPException(
            status_code=422, detail=f"Invalid range. Use one of: {', '.join(_VALID_RANGES)}"
        )
    try:
        return indicator_service.get_indicators(db, provider, ticker, range)
    except InvalidTickerError:
        raise HTTPException(status_code=404, detail=f"Unknown ticker: {ticker}") from None
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=f"Data provider error: {exc}") from exc


@router.get("/{ticker}/risk", response_model=RiskOut)
def get_risk(
    ticker: str,
    range: str = Query("6m", description=f"One of: {', '.join(_VALID_RANGES)}"),
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis),
    provider: MarketDataProvider = Depends(get_provider),
) -> dict:
    if range not in _VALID_RANGES:
        raise HTTPException(
            status_code=422, detail=f"Invalid range. Use one of: {', '.join(_VALID_RANGES)}"
        )
    try:
        return risk_service.get_risk(db, redis, provider, ticker, range)
    except InvalidTickerError:
        raise HTTPException(status_code=404, detail=f"Unknown ticker: {ticker}") from None
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=f"Data provider error: {exc}") from exc


@router.get("/{ticker}/sentiment", response_model=SentimentOut)
def get_sentiment(
    ticker: str,
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis),
    provider: MarketDataProvider = Depends(get_provider),
) -> dict:
    try:
        return sentiment_service.get_sentiment(db, redis, provider, ticker)
    except InvalidTickerError:
        raise HTTPException(status_code=404, detail=f"Unknown ticker: {ticker}") from None
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=f"Data provider error: {exc}") from exc
