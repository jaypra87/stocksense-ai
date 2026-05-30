from fastapi import APIRouter

from app.api.v1 import (
    alerts,
    auth,
    backtests,
    health,
    models,
    predictions,
    stocks,
    watchlist,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(stocks.router)
api_router.include_router(predictions.router)
api_router.include_router(watchlist.router)
api_router.include_router(alerts.router)
api_router.include_router(backtests.router)
api_router.include_router(models.router)
