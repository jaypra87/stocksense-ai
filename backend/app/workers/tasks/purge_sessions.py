"""Scheduled task: delete expired sessions and the guests they orphan."""

import logging

from app.db.session import system_session
from app.services import auth_service
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.tasks.purge_sessions.purge_sessions")
def purge_sessions() -> dict:
    db = system_session()
    try:
        result = auth_service.purge_expired(db)
        logger.info("purged: %s", result)
        return result
    finally:
        db.close()
