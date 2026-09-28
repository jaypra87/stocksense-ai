from functools import lru_cache

from redis import Redis

from app.core.config import get_settings


@lru_cache
def get_redis() -> Redis:
    settings = get_settings()
    # Bounded timeouts matter because the cache is optional (see cache.py):
    # an unreachable-but-not-refusing Redis host must cost us ~2s once, not a
    # hung request. Connection errors then surface as RedisError, which the
    # cache layer and rate limiter both handle by failing open.
    return Redis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_connect_timeout=settings.redis_timeout_seconds,
        socket_timeout=settings.redis_timeout_seconds,
        retry_on_timeout=False,
        health_check_interval=30,
    )
