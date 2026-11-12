import logging

from fastapi import APIRouter, Depends, Request
from redis import Redis
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.cache.redis_client import get_redis
from app.core.client_ip import client_ip, via_trusted_proxy
from app.db.session import get_db

router = APIRouter(tags=["health"])

logger = logging.getLogger("stocksense.health")


@router.get("/health")
def health() -> dict[str, str]:
    """Liveness. Deliberately dependency-free so the platform's health check
    (and the frontend's pre-warm ping) can't be blocked by Postgres or Redis."""
    return {"status": "ok"}


@router.get("/health/deep")
def health_deep(
    request: Request,
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> dict[str, str]:
    """Reports Postgres and Redis reachability.

    Returns 200 with a per-component verdict rather than raising, so a dead
    dependency is *diagnosable* from the response instead of collapsing into an
    opaque 500. Postgres is required (status "error" if down); Redis is only a
    cache, so losing it is "degraded", not a failure.

    `proxy` says whether this request arrived with a valid proxy secret. Called
    through the frontend it must be "trusted"; "direct" there means the secret
    on the frontend and the backend differ, and every visitor is then sharing
    one rate-limit bucket. `client` is the address the limiter would charge
    for this request: the caller's own IP, so nothing is disclosed.
    """
    components: dict[str, str] = {
        "proxy": "trusted" if via_trusted_proxy(request) else "direct",
        "client": client_ip(request),
    }

    try:
        db.execute(text("SELECT 1"))
        components["postgres"] = "ok"
    except Exception as exc:  # noqa: BLE001 — any driver error means "not reachable"
        logger.warning("health: postgres unreachable: %s", exc)
        components["postgres"] = "unavailable"

    try:
        redis.ping()
        components["redis"] = "ok"
    except Exception as exc:  # noqa: BLE001 — redis-py raises several error types
        logger.warning("health: redis unreachable: %s", exc)
        components["redis"] = "unavailable"

    if components["postgres"] != "ok":
        status = "error"
    elif components["redis"] != "ok":
        status = "degraded"
    else:
        status = "ok"

    return {"status": status, **components}
