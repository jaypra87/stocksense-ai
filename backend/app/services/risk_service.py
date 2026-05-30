"""Orchestrates the standalone /risk endpoint: compute indicators -> score risk
-> persist a snapshot -> return.

Note: standalone risk is *market* risk (volatility, drawdown, volume, trend).
The risk attached to a prediction additionally folds in model uncertainty.
"""

from redis import Redis
from sqlalchemy.orm import Session

from app.db.models.risk_snapshot import RiskSnapshot
from app.services import indicator_service, sentiment_service, stock_service
from app.services.market_data.base import MarketDataProvider
from app.services.risk import compute_risk

NOTE = "Risk is an educational signal, not advice. Not financial advice."


def get_risk(
    db: Session, redis: Redis, provider: MarketDataProvider, raw_ticker: str, range_: str = "6m"
) -> dict:
    ticker = stock_service.normalize_ticker(raw_ticker)
    indicators = indicator_service.get_indicators(db, provider, ticker, range_)
    news_score = sentiment_service.sentiment_score(db, redis, provider, ticker)

    risk = compute_risk(
        indicators["latest"], indicators["signals"], sentiment_score=news_score
    )
    _store(db, ticker, risk)

    return {
        "ticker": ticker,
        "risk_score": risk["risk_score"],
        "risk_level": risk["risk_level"],
        "factors": risk["factors"],
        "as_of": indicators["latest"]["timestamp"],
        "note": NOTE,
    }


def _store(db: Session, ticker: str, risk: dict) -> None:
    db.add(
        RiskSnapshot(
            ticker=ticker,
            risk_level=risk["risk_level"],
            risk_score=risk["risk_score"],
            factors_json=risk["factors"],
        )
    )
    db.commit()
