"""Daily token budgets: one per user, one for the whole deployment.

The limits bound the bill on a public demo, so they count the tokens the API
actually reports after each turn rather than a guess made before it. A dead
Redis fails open: the budget is cost control, not access control, and the
per-IP rate limit still stands.
"""

import logging
import uuid
from datetime import UTC, datetime

from redis import Redis, RedisError

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_TTL = 2 * 24 * 3600


class BudgetExceeded(Exception):
    def __init__(self, scope: str) -> None:
        self.scope = scope
        super().__init__(f"{scope} daily token budget exhausted")


def _day() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d")


def _keys(user_id: uuid.UUID) -> tuple[str, str]:
    day = _day()
    return f"stockman:tokens:{day}:user:{user_id}", f"stockman:tokens:{day}:global"


def usage(redis: Redis, user_id: uuid.UUID) -> tuple[int, int]:
    user_key, global_key = _keys(user_id)
    try:
        return int(str(redis.get(user_key) or 0)), int(str(redis.get(global_key) or 0))
    except RedisError as exc:
        logger.warning("stockman budget: Redis unavailable (%s); not enforcing", exc)
        return 0, 0


def check(redis: Redis, user_id: uuid.UUID) -> None:
    settings = get_settings()
    user_used, global_used = usage(redis, user_id)
    if user_used >= settings.stockman_user_daily_tokens:
        raise BudgetExceeded("user")
    if global_used >= settings.stockman_global_daily_tokens:
        raise BudgetExceeded("global")


def charge(redis: Redis, user_id: uuid.UUID, tokens: int) -> None:
    if tokens <= 0:
        return
    try:
        for key in _keys(user_id):
            if redis.incrby(key, tokens) == tokens:
                redis.expire(key, _TTL)
    except RedisError as exc:
        logger.warning("stockman budget: could not record %d tokens (%s)", tokens, exc)
