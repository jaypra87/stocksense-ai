"""Import all models here so Alembic's autogenerate sees them via Base.metadata."""

from app.db.models.alert import Alert, AlertEvent
from app.db.models.backtest import Backtest
from app.db.models.model_artifact import ModelArtifact
from app.db.models.prediction import Prediction
from app.db.models.price_candle import PriceCandle
from app.db.models.risk_snapshot import RiskSnapshot
from app.db.models.sentiment_snapshot import SentimentSnapshot
from app.db.models.stock import Stock
from app.db.models.technical_indicator import TechnicalIndicator
from app.db.models.user import User
from app.db.models.watchlist import WatchlistItem

__all__ = [
    "Alert",
    "AlertEvent",
    "Backtest",
    "ModelArtifact",
    "Prediction",
    "PriceCandle",
    "RiskSnapshot",
    "SentimentSnapshot",
    "Stock",
    "TechnicalIndicator",
    "User",
    "WatchlistItem",
]
