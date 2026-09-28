"""Read-through cache helper.

`cached_json` is the get-or-set pattern: return the cached value if present,
otherwise call `producer()`, store its (JSON-serializable) result, and return it.
This is our primary defense against hammering the market-data provider.

Fail-open by design: Redis is a *cache*, never a source of truth. If it is
unreachable (unset REDIS_URL, expired free-tier instance, network blip) every
cached endpoint must still serve real data, just without the speed-up. Before
this, a dead Redis turned `redis.get` into an unhandled RedisError and every
cached route — quote, metadata, search, sentiment — returned a 500.
"""

import json
import logging
from collections.abc import Callable
from typing import Any

from redis import Redis, RedisError

logger = logging.getLogger("stocksense.cache")

# A dead Redis would otherwise log once per key per request; this keeps the
# signal (you still learn the cache is down) without flooding the log.
_outage_logged = False


def _note_outage(action: str, key: str, exc: Exception) -> None:
    global _outage_logged
    if not _outage_logged:
        logger.warning(
            "Redis unavailable (%s %s): %s — serving uncached. "
            "Check REDIS_URL; the app stays correct but slower.",
            action, key, exc,
        )
        _outage_logged = True


def _note_recovery() -> None:
    global _outage_logged
    if _outage_logged:
        logger.info("Redis reachable again; caching resumed.")
        _outage_logged = False


def cached_json(
    redis: Redis,
    key: str,
    ttl: int,
    producer: Callable[[], Any],
) -> Any:
    try:
        cached = redis.get(key)
        _note_recovery()
    except RedisError as exc:
        _note_outage("get", key, exc)
        return producer()

    if cached is not None:
        try:
            return json.loads(cached)
        except ValueError:
            # Corrupt/legacy entry: drop it and regenerate rather than 500.
            logger.warning("Discarding unparseable cache entry %s", key)

    value = producer()
    try:
        redis.set(key, json.dumps(value, default=str), ex=ttl)
    except RedisError as exc:
        _note_outage("set", key, exc)
    return value
