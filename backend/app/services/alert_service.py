"""Alert CRUD + the evaluation engine.

`evaluate_alerts` is a plain function so it's fully testable without Celery; the
scheduled task (app/workers/tasks/check_alerts.py) is just a thin wrapper around it.
"""

import logging
import uuid
from datetime import UTC, datetime, timedelta

from redis import Redis
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.alert import Alert, AlertEvent
from app.services import risk_service, stock_service
from app.services.market_data.base import MarketDataProvider, ProviderError

logger = logging.getLogger(__name__)

# Don't re-fire the same alert more often than this.
_COOLDOWN = timedelta(hours=6)


# --- CRUD ---


def list_alerts(db: Session, user_id: uuid.UUID) -> list[dict]:
    rows = db.execute(
        select(Alert).where(Alert.user_id == user_id).order_by(Alert.created_at.desc())
    ).scalars().all()
    return [_alert_dict(a) for a in rows]


def create_alert(
    db: Session, user_id: uuid.UUID, ticker: str, alert_type: str, threshold: float
) -> dict:
    ticker = stock_service.ensure_stock(db, ticker)
    alert = Alert(user_id=user_id, ticker=ticker, alert_type=alert_type, threshold=threshold)
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return _alert_dict(alert)


def update_alert(
    db: Session, user_id: uuid.UUID, alert_id: uuid.UUID, **changes
) -> dict | None:
    alert = db.get(Alert, alert_id)
    if alert is None or alert.user_id != user_id:
        return None
    if changes.get("threshold") is not None:
        alert.threshold = changes["threshold"]
    if changes.get("active") is not None:
        alert.active = changes["active"]
    db.commit()
    db.refresh(alert)
    return _alert_dict(alert)


def delete_alert(db: Session, user_id: uuid.UUID, alert_id: uuid.UUID) -> bool:
    alert = db.get(Alert, alert_id)
    if alert is None or alert.user_id != user_id:
        return False
    db.delete(alert)
    db.commit()
    return True


def list_events(db: Session, user_id: uuid.UUID, limit: int = 50) -> list[dict]:
    rows = db.execute(
        select(AlertEvent, Alert)
        .join(Alert, Alert.id == AlertEvent.alert_id)
        .where(Alert.user_id == user_id)
        .order_by(AlertEvent.triggered_at.desc())
        .limit(limit)
    ).all()
    return [
        {
            "id": str(event.id),
            "alert_id": str(event.alert_id),
            "ticker": alert.ticker,
            "alert_type": alert.alert_type,
            "triggered_at": event.triggered_at.isoformat() if event.triggered_at else None,
            "payload": event.payload,
        }
        for event, alert in rows
    ]


# --- Evaluation engine (called by the scheduled task) ---


def evaluate_alerts(db: Session, redis: Redis, provider: MarketDataProvider) -> dict:
    """Check every active alert; record an AlertEvent for any that fire."""
    alerts = db.execute(select(Alert).where(Alert.active.is_(True))).scalars().all()
    now = datetime.now(UTC)
    quote_cache: dict[str, dict] = {}
    risk_cache: dict[str, dict] = {}
    triggered = 0

    for alert in alerts:
        if not _cooldown_ok(alert, now):
            continue
        try:
            value, fired = _check(alert, provider, redis, db, quote_cache, risk_cache)
        except ProviderError as exc:
            logger.warning("alert %s skipped (provider error): %s", alert.id, exc)
            continue
        if fired:
            _record_event(db, alert, value, now)
            triggered += 1

    db.commit()
    return {"checked": len(alerts), "triggered": triggered}


def _check(alert, provider, redis, db, quote_cache, risk_cache) -> tuple[float, bool]:
    t = alert.ticker
    if alert.alert_type in ("price_above", "price_below", "pct_change_above"):
        if t not in quote_cache:
            quote_cache[t] = stock_service.get_quote(redis, provider, t)
        quote = quote_cache[t]
        if alert.alert_type == "price_above":
            return quote["price"], quote["price"] > alert.threshold
        if alert.alert_type == "price_below":
            return quote["price"], quote["price"] < alert.threshold
        pct = abs(quote.get("change_percent") or 0.0)
        return pct, pct > alert.threshold

    if alert.alert_type == "risk_above":
        if t not in risk_cache:
            risk_cache[t] = risk_service.get_risk(db, redis, provider, t)
        score = risk_cache[t]["risk_score"]
        return score, score > alert.threshold

    return 0.0, False


def _cooldown_ok(alert: Alert, now: datetime) -> bool:
    return alert.last_triggered_at is None or (now - alert.last_triggered_at) > _COOLDOWN


def _record_event(db: Session, alert: Alert, value: float, now: datetime) -> None:
    message = (
        f"{alert.ticker} {alert.alert_type.replace('_', ' ')} {alert.threshold} "
        f"(current {round(value, 2)})"
    )
    db.add(
        AlertEvent(
            alert_id=alert.id,
            payload={"value": round(value, 4), "threshold": alert.threshold, "message": message},
        )
    )
    alert.last_triggered_at = now


def _alert_dict(a: Alert) -> dict:
    return {
        "id": str(a.id),
        "ticker": a.ticker,
        "alert_type": a.alert_type,
        "threshold": a.threshold,
        "active": a.active,
        "last_triggered_at": a.last_triggered_at.isoformat() if a.last_triggered_at else None,
        "created_at": a.created_at.isoformat() if a.created_at else None,
    }
