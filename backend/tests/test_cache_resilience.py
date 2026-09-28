"""Redis must be optional.

This is a regression suite for a production outage: Redis was unreachable on the
deployed backend, `cached_json` called `redis.get()` with no error handling, and
the RedisError propagated as a 500 out of every cached route — quote, metadata,
search and sentiment. The UI read that as "invalid ticker" and the whole app
looked dead, even though Postgres, the provider and the uncached routes (chart,
indicators) were all healthy.

The existing endpoint tests couldn't catch it because they run against a local
Redis that is always up. These assert the *absence* of Redis instead.
"""

import pytest
from fastapi.testclient import TestClient
from redis import ConnectionError as RedisConnectionError
from redis.exceptions import RedisError

from app.api.deps import get_current_user
from app.cache.cache import cached_json
from app.cache.redis_client import get_redis
from app.main import app
from app.services.market_data.fake_provider import FakeProvider
from app.services.market_data.registry import get_provider
from tests.conftest import make_user


class BrokenRedis:
    """Stands in for an unreachable Redis: every command raises."""

    def get(self, *args: object, **kwargs: object) -> None:
        raise RedisConnectionError("Error 111 connecting to localhost:6379. Connection refused.")

    def set(self, *args: object, **kwargs: object) -> None:
        raise RedisConnectionError("Error 111 connecting to localhost:6379. Connection refused.")

    def ping(self, *args: object, **kwargs: object) -> None:
        raise RedisConnectionError("Error 111 connecting to localhost:6379. Connection refused.")

    def incr(self, *args: object, **kwargs: object) -> None:
        raise RedisConnectionError("Error 111 connecting to localhost:6379. Connection refused.")


@pytest.fixture
def no_redis_client() -> TestClient:
    app.dependency_overrides[get_provider] = lambda: FakeProvider()
    app.dependency_overrides[get_redis] = lambda: BrokenRedis()
    app.dependency_overrides[get_current_user] = lambda: make_user()
    yield TestClient(app)
    app.dependency_overrides.clear()


# --- the unit that broke -----------------------------------------------------


def test_cached_json_falls_back_to_producer_when_redis_is_down() -> None:
    value = cached_json(BrokenRedis(), "any:key", 60, lambda: {"ok": True})
    assert value == {"ok": True}


def test_cached_json_still_returns_when_only_the_write_fails() -> None:
    class ReadOnlyBroken(BrokenRedis):
        def get(self, *args: object, **kwargs: object) -> None:
            return None  # cache miss, not an error

    assert cached_json(ReadOnlyBroken(), "k", 60, lambda: [1, 2]) == [1, 2]


def test_cached_json_regenerates_on_a_corrupt_entry() -> None:
    class CorruptRedis(BrokenRedis):
        def get(self, *args: object, **kwargs: object) -> str:
            return "{not json"

        def set(self, *args: object, **kwargs: object) -> None:
            return None

    assert cached_json(CorruptRedis(), "k", 60, lambda: {"fresh": 1}) == {"fresh": 1}


def test_producer_errors_are_not_swallowed() -> None:
    """Failing open applies to the cache, not to the data source behind it."""

    def boom() -> None:
        raise ValueError("upstream exploded")

    with pytest.raises(ValueError, match="upstream exploded"):
        cached_json(BrokenRedis(), "k", 60, boom)


# --- the routes that 500'd ---------------------------------------------------


def test_quote_endpoint_survives_redis_outage(no_redis_client: TestClient) -> None:
    resp = no_redis_client.get("/api/v1/stocks/NVDA/quote")
    assert resp.status_code == 200, resp.text
    assert resp.json()["price"] > 0


def test_search_endpoint_survives_redis_outage(no_redis_client: TestClient) -> None:
    resp = no_redis_client.get("/api/v1/stocks/search", params={"q": "apple"})
    assert resp.status_code == 200, resp.text
    assert "AAPL" in [r["symbol"] for r in resp.json()]


def test_login_still_works_when_the_rate_limiter_has_no_redis(
    no_redis_client: TestClient,
) -> None:
    """The limiter already failed open; keep it that way (bad creds, not a 500)."""
    resp = no_redis_client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "wrong-password-12345"},
    )
    assert resp.status_code == 401, resp.text


# --- diagnosability ----------------------------------------------------------


def test_deep_health_reports_redis_as_degraded_instead_of_raising(
    no_redis_client: TestClient,
) -> None:
    resp = no_redis_client.get("/api/v1/health/deep")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["redis"] == "unavailable"
    assert body["status"] in {"degraded", "error"}


def test_redis_error_is_the_base_class_we_catch() -> None:
    """Guards the `except RedisError` in cache.py against a narrower catch."""
    assert issubclass(RedisConnectionError, RedisError)
