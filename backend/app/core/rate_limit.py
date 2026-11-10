"""Fixed-window rate limiting.

Primary store is Redis so limits hold across instances. When Redis is
unreachable the limiter used to fail open, which on the live deployment
meant *no* limit at all for as long as the cache was misconfigured. It now
falls back to an in-process window: weaker (per instance, lost on restart)
but never absent. Recovery is automatic: the next request that reaches Redis
uses it again.
"""

import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request, status
from redis import Redis, RedisError

from app.cache.redis_client import get_redis
from app.core.client_ip import client_ip

logger = logging.getLogger("stocksense.ratelimit")


@dataclass
class Verdict:
    allowed: bool
    retry_after: int  # seconds until the window resets (0 when allowed)


class _LocalWindows:
    """Thread-safe fixed windows in process memory: {key: (count, reset_at)}."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._windows: dict[str, tuple[int, float]] = {}
        self._last_prune = 0.0

    def hit(self, key: str, limit: int, window: int) -> Verdict:
        now = time.monotonic()
        with self._lock:
            if now - self._last_prune > 60:
                self._windows = {k: v for k, v in self._windows.items() if v[1] > now}
                self._last_prune = now
            count, reset_at = self._windows.get(key, (0, now + window))
            if reset_at <= now:
                count, reset_at = 0, now + window
            count += 1
            self._windows[key] = (count, reset_at)
        if count > limit:
            return Verdict(False, max(1, int(reset_at - now)))
        return Verdict(True, 0)


_local = _LocalWindows()
_fallback_logged = False


class RateLimiter:
    def __init__(self, name: str, limit: int, window_seconds: int) -> None:
        self.name = name
        self.limit = limit
        self.window = window_seconds

    def check(self, redis: Redis, ip: str) -> Verdict:
        global _fallback_logged
        key = f"ratelimit:{self.name}:{ip}"
        try:
            count = redis.incr(key)
            if count == 1:
                redis.expire(key, self.window)
            if _fallback_logged:
                logger.info("Rate limiter back on Redis")
                _fallback_logged = False
            if count > self.limit:
                ttl = redis.ttl(key)
                return Verdict(False, ttl if ttl and ttl > 0 else self.window)
            return Verdict(True, 0)
        except RedisError as exc:
            if not _fallback_logged:
                logger.warning(
                    "Rate limiter: Redis unavailable (%s); using in-process windows", exc
                )
                _fallback_logged = True
            return _local.hit(key, self.limit, self.window)

    def __call__(self, request: Request, redis: Redis = Depends(get_redis)) -> None:
        verdict = self.check(redis, client_ip(request))
        if not verdict.allowed:
            raise too_many_requests(verdict.retry_after)


def too_many_requests(retry_after: int, challenge: bool = False) -> HTTPException:
    detail: dict = {"message": "Too many attempts. Please try again later."}
    if challenge:
        detail["challenge"] = "turnstile"
    return HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail=detail,
        headers={"Retry-After": str(retry_after)},
    )


def rate_limit(name: str, limit: int, window_seconds: int) -> Callable:
    """Dependency factory: allow `limit` requests per `window_seconds` per IP."""
    return RateLimiter(name, limit, window_seconds)
