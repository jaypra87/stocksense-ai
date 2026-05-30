from fastapi import APIRouter, Depends
from redis import Redis
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.cache.redis_client import get_redis
from app.db.session import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/deep")
def health_deep(
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> dict[str, str]:
    """Verifies Postgres and Redis are reachable. Used by deploy platforms / monitors."""
    db.execute(text("SELECT 1"))
    redis.ping()
    return {"status": "ok", "postgres": "ok", "redis": "ok"}
