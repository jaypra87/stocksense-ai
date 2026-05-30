"""Celery application + beat schedule.

Run a worker:   celery -A app.workers.celery_app worker --loglevel=info
Run the beat:   celery -A app.workers.celery_app beat   --loglevel=info

Both use Redis (already running) as broker + result backend.
"""

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "stocksense",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.tasks.check_alerts"],
)

celery_app.conf.update(
    timezone="UTC",
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    beat_schedule={
        "check-alerts-every-minute": {
            "task": "app.workers.tasks.check_alerts.check_alerts",
            "schedule": 60.0,  # seconds
        },
    },
)
