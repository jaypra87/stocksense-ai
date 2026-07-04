"""Tests for the security hardening: settings validation, rate limiting,
security headers, and sanitized error responses."""

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.rate_limit import rate_limit
from app.main import app


class FakeRequest:
    """Minimal stand-in for fastapi.Request in limiter unit tests."""

    def __init__(self, ip: str = "203.0.113.7", forwarded: str | None = None):
        self.headers = {"x-forwarded-for": forwarded} if forwarded else {}
        self.client = type("Client", (), {"host": ip})()


class FakeRedis:
    """In-memory INCR/EXPIRE/TTL, enough to drive the fixed-window limiter."""

    def __init__(self):
        self.counts: dict[str, int] = {}

    def incr(self, key: str) -> int:
        self.counts[key] = self.counts.get(key, 0) + 1
        return self.counts[key]

    def expire(self, key: str, seconds: int) -> None:
        pass

    def ttl(self, key: str) -> int:
        return 42


def test_production_rejects_default_jwt_secret() -> None:
    with pytest.raises(ValueError, match="JWT_SECRET"):
        Settings(environment="production", jwt_secret="change-me-in-prod", _env_file=None)


def test_production_rejects_short_jwt_secret() -> None:
    with pytest.raises(ValueError, match="32"):
        Settings(environment="production", jwt_secret="short", _env_file=None)


def test_production_accepts_strong_jwt_secret() -> None:
    s = Settings(environment="production", jwt_secret="x" * 48, _env_file=None)
    assert s.environment == "production"


def test_development_allows_default_secret() -> None:
    s = Settings(environment="development", jwt_secret="change-me-in-prod", _env_file=None)
    assert s.environment == "development"


def test_rate_limit_blocks_after_threshold() -> None:
    limiter = rate_limit("test", limit=3, window_seconds=60)
    redis = FakeRedis()
    request = FakeRequest()

    for _ in range(3):
        limiter(request, redis)  # under the limit: no exception

    with pytest.raises(HTTPException) as excinfo:
        limiter(request, redis)
    assert excinfo.value.status_code == 429
    assert excinfo.value.headers["Retry-After"] == "42"


def test_rate_limit_uses_forwarded_ip() -> None:
    limiter = rate_limit("fwd", limit=1, window_seconds=60)
    redis = FakeRedis()

    limiter(FakeRequest(forwarded="198.51.100.1, 10.0.0.1"), redis)
    # A different forwarded IP gets its own bucket.
    limiter(FakeRequest(forwarded="198.51.100.2"), redis)
    with pytest.raises(HTTPException):
        limiter(FakeRequest(forwarded="198.51.100.1"), redis)


def test_security_headers_present() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/health")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert "permissions-policy" in response.headers
