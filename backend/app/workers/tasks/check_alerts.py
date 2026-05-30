"""Scheduled task: evaluate all active alerts.

Thin wrapper around alert_service.evaluate_alerts so the real logic stays
testable without Celery. Manages its own DB session (tasks run outside requests).
"""

import logging

from app.cache.redis_client import get_redis
from app.db.session import SessionLocal
from app.services import alert_service
from app.services.market_data.registry import get_provider
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.tasks.check_alerts.check_alerts")
def check_alerts() -> dict:
    db = SessionLocal()
    try:
        result = alert_service.evaluate_alerts(db, get_redis(), get_provider())
        logger.info("alert check: %s", result)
        return result
    finally:
        db.close()
