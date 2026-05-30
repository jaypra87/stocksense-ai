"""Serves predictions: load active model -> build latest features -> predict
-> assemble an explainable, uncertainty-aware response -> store it.

Always attaches the educational disclaimer (non-negotiable product rule).
"""

import numpy as np
from redis import Redis
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.model_artifact import ModelArtifact
from app.db.models.prediction import Prediction
from app.ml import registry
from app.ml.explain import top_contributions, uncertainty_note
from app.ml.features import HORIZON_DAYS, candles_to_frame, latest_feature_row
from app.ml.registry import NoModelError
from app.ml.training import predict_return_range
from app.services import indicator_service, sentiment_service, stock_service
from app.services.indicators import compute_indicators
from app.services.market_data.base import MarketDataProvider
from app.services.risk import compute_risk

DISCLAIMER = "Educational forecast only. Not financial advice."


def predict(
    db: Session, redis: Redis, provider: MarketDataProvider, raw_ticker: str, horizon: str
) -> dict:
    if horizon not in HORIZON_DAYS:
        raise ValueError(f"unsupported horizon: {horizon}")

    ticker = stock_service.normalize_ticker(raw_ticker)
    bundle, version = _load_active(db, horizon)

    # Build the most recent feature row from fresh daily candles.
    candles = stock_service.fetch_and_store_candles(db, provider, ticker, "1y", "1d")
    ind = compute_indicators(candles_to_frame(candles))
    X = latest_feature_row(ind, bundle.feature_names)
    last_close = float(candles[-1].close)

    # Classification: trend + confidence + full class distribution.
    proba = bundle.classifier.predict_proba(X)[0]
    classes = list(bundle.classifier.classes_)
    class_probs = {c: round(float(p), 4) for c, p in zip(classes, proba, strict=True)}
    trend = classes[int(np.argmax(proba))]
    confidence = round(float(np.max(proba)), 4)

    # Regression: expected return range (point ± forest spread) -> price range.
    ret_mean, ret_low, ret_high = predict_return_range(bundle.regressor, X)
    expected_low = round(last_close * (1 + ret_low), 2)
    expected_high = round(last_close * (1 + ret_high), 2)

    # Per-prediction explanation + uncertainty messaging.
    top_factors = top_contributions(bundle, X)

    # Risk: market risk + model uncertainty + news sentiment (best-effort).
    latest = indicator_service.latest_snapshot(ind)
    signals = indicator_service.signals(ind)
    news_score = sentiment_service.sentiment_score(db, redis, provider, ticker)
    risk = compute_risk(latest, signals, confidence=confidence, sentiment_score=news_score)
    notes = uncertainty_note(confidence, class_probs, latest.get("volatility_30"))

    explanation = {
        "top_factors": top_factors,
        "class_probabilities": class_probs,
        "expected_return_mean": round(ret_mean, 5),
        "risk_level": risk["risk_level"],
        "risk_factors": risk["factors"],
        "notes": notes,
    }

    _store(
        db,
        ticker=ticker,
        horizon=horizon,
        trend=trend,
        confidence=confidence,
        ret_low=round(ret_low, 5),
        ret_high=round(ret_high, 5),
        price_low=expected_low,
        price_high=expected_high,
        risk_score=risk["risk_score"],
        version=version,
        explanation=explanation,
    )

    return {
        "ticker": ticker,
        "horizon": horizon,
        "trend": trend,
        "confidence": confidence,
        "expected_return_low": round(ret_low, 5),
        "expected_return_high": round(ret_high, 5),
        "expected_low": expected_low,
        "expected_high": expected_high,
        "last_close": last_close,
        "risk_score": risk["risk_score"],
        "risk_level": risk["risk_level"],
        "risk_factors": risk["factors"],
        "model_version": version,
        "class_probabilities": class_probs,
        "top_factors": top_factors,
        "notes": notes,
        "disclaimer": DISCLAIMER,
    }


def get_history(db: Session, raw_ticker: str, horizon: str | None, limit: int = 50) -> list[dict]:
    ticker = stock_service.normalize_ticker(raw_ticker)
    stmt = select(Prediction).where(Prediction.ticker == ticker)
    if horizon:
        stmt = stmt.where(Prediction.horizon == horizon)
    stmt = stmt.order_by(Prediction.created_at.desc()).limit(limit)

    rows = db.execute(stmt).scalars().all()
    return [
        {
            "id": str(r.id),
            "ticker": r.ticker,
            "horizon": r.horizon,
            "trend": r.trend,
            "confidence": r.confidence,
            "expected_low": r.expected_low,
            "expected_high": r.expected_high,
            "model_version": r.model_version,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


# --- helpers ---


def _load_active(db: Session, horizon: str) -> tuple[registry.ModelBundle, str]:
    artifact = db.execute(
        select(ModelArtifact).where(
            ModelArtifact.horizon == horizon, ModelArtifact.is_active.is_(True)
        )
    ).scalar_one_or_none()
    if artifact is None:
        raise NoModelError(f"no active model for horizon {horizon}")
    return registry.load_bundle(artifact.path), artifact.model_version


def _store(db: Session, **kw) -> None:
    db.add(
        Prediction(
            ticker=kw["ticker"],
            horizon=kw["horizon"],
            trend=kw["trend"],
            confidence=kw["confidence"],
            expected_return_low=kw["ret_low"],
            expected_return_high=kw["ret_high"],
            expected_low=kw["price_low"],
            expected_high=kw["price_high"],
            risk_score=kw["risk_score"],
            model_version=kw["version"],
            explanation=kw["explanation"],
        )
    )
    db.commit()
