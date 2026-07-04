"""Fixed-window rate limiting backed by Redis.

Used on the auth endpoints to slow brute-force and credential-stuffing
attempts. Fails open: if Redis is unreachable the request proceeds (login
availability beats strict limiting for this app's threat model).
"""

import logging
from collections.abc import Callable

from fastapi import Depends, HTTPException, Request, status
from redis import Redis, RedisError

from app.cache.redis_client import get_redis

logger = logging.getLogger("stocksense.ratelimit")


def _client_ip(request: Request) -> str:
    """Client IP, preferring the proxy-supplied X-Forwarded-For (Render/Vercel
    terminate TLS in front of the app, so request.client is the proxy)."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def rate_limit(name: str, limit: int, window_seconds: int) -> Callable:
    """Dependency factory: allow `limit` requests per `window_seconds` per IP."""

    def dependency(request: Request, redis: Redis = Depends(get_redis)) -> None:
        key = f"ratelimit:{name}:{_client_ip(request)}"
        try:
            count = redis.incr(key)
            if count == 1:
                redis.expire(key, window_seconds)
            if count > limit:
                ttl = redis.ttl(key)
                retry_after = ttl if ttl and ttl > 0 else window_seconds
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many attempts. Please try again later.",
                    headers={"Retry-After": str(retry_after)},
                )
        except RedisError:
            logger.warning("Rate limiter unavailable (Redis error); failing open")

    return dependency
