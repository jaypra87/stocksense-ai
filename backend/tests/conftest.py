import uuid

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.cache.redis_client import get_redis
from app.db.models.user import User
from app.main import app


class InMemoryRedis:
    """Enough Redis for the cache and the fixed-window limiter, per test.

    Endpoint tests used to share the developer's real Redis, which made the
    rate-limited routes order- and history-dependent: the signup limiter allows
    5 per hour per IP, so the sixth *test run* within the hour started getting
    429s instead of the status under test. A fresh instance per test keeps the
    suite hermetic and lets it run with no Redis installed at all.
    """

    def __init__(self) -> None:
        self.store: dict[str, str] = {}
        self.counters: dict[str, int] = {}

    def get(self, key: str) -> str | None:
        return self.store.get(key)

    def set(self, key: str, value: str, ex: int | None = None) -> None:
        self.store[key] = value

    def incr(self, key: str) -> int:
        self.counters[key] = self.counters.get(key, 0) + 1
        return self.counters[key]

    def expire(self, key: str, seconds: int) -> None:
        pass

    def ttl(self, key: str) -> int:
        return 60

    def ping(self) -> bool:
        return True


@pytest.fixture
def client() -> TestClient:
    app.dependency_overrides[get_redis] = lambda: InMemoryRedis()
    yield TestClient(app)
    app.dependency_overrides.pop(get_redis, None)


def make_user(email: str = "tester@example.com") -> User:
    """A User instance that never touches the database.

    Endpoint tests care about *authorization* (which user the request acts as),
    not about how the row got there, so a detached model is enough.
    """
    return User(id=uuid.uuid4(), email=email, password_hash="x", preferences={})


@pytest.fixture
def as_user():
    """Authenticate the TestClient as a given user for the duration of a test.

    The data routers declare `Depends(get_current_user)` at router level, so
    overriding that one dependency is what stands in for a bearer token.
    Returns the user, so tests can assert against its id.
    """
    created: list[User] = []

    def _login(user: User | None = None) -> User:
        user = user or make_user()
        app.dependency_overrides[get_current_user] = lambda: user
        created.append(user)
        return user

    yield _login
    app.dependency_overrides.pop(get_current_user, None)
