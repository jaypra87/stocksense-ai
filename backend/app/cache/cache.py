"""Read-through cache helper.

`cached_json` is the get-or-set pattern: return the cached value if present,
otherwise call `producer()`, store its (JSON-serializable) result, and return it.
This is our primary defense against hammering the market-data provider.
"""

import json
from collections.abc import Callable
from typing import Any

from redis import Redis


def cached_json(
    redis: Redis,
    key: str,
    ttl: int,
    producer: Callable[[], Any],
) -> Any:
    cached = redis.get(key)
    if cached is not None:
        return json.loads(cached)

    value = producer()
    redis.set(key, json.dumps(value, default=str), ex=ttl)
    return value
