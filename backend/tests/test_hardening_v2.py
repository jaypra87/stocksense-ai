"""Unit tests for the new defensive pieces: encryption, client IP, the
rate-limiter fallback, the Origin check, and Turnstile gating."""

import pytest
from fastapi.testclient import TestClient
from redis import RedisError

from app.cache.redis_client import get_redis
from app.core import turnstile
from app.core.client_ip import client_ip
from app.core.config import get_settings
from app.core.crypto import decrypt_email, encrypt_email, hash_email, is_encrypted
from app.core.rate_limit import RateLimiter
from app.main import app
from tests.conftest import InMemoryRedis

# --- crypto -----------------------------------------------------------------


def test_email_encryption_roundtrip_and_normalisation() -> None:
    blob = encrypt_email("  Person@Example.COM ")
    assert is_encrypted(blob)
    assert decrypt_email(blob) == "person@example.com"
    assert not is_encrypted("person@example.com")


def test_email_ciphertext_is_randomised_but_hash_is_stable() -> None:
    assert encrypt_email("a@b.co") != encrypt_email("a@b.co")
    assert hash_email("A@B.CO") == hash_email("a@b.co")
    assert hash_email("a@b.co") != hash_email("a@b.com")


# --- client ip --------------------------------------------------------------


class _Req:
    def __init__(self, headers: dict, host: str = "10.0.0.9") -> None:
        self.headers = headers
        self.client = type("C", (), {"host": host})()


def test_client_ip_ignores_the_spoofable_leftmost_forwarded_entry() -> None:
    # (Routable addresses: Python treats the RFC 5737 documentation ranges
    # as private, and the resolver skips private hops on purpose.)
    req = _Req({"x-forwarded-for": "1.1.1.1, 93.184.216.34"})
    assert client_ip(req) == "93.184.216.34"


def test_client_ip_trusts_the_proxy_header_only_with_the_secret(monkeypatch) -> None:
    monkeypatch.setattr(get_settings(), "proxy_shared_secret", "s3cret")
    with_secret = _Req({"x-proxy-secret": "s3cret", "x-client-ip": "198.51.100.4",
                        "x-forwarded-for": "9.9.9.9"})
    assert client_ip(with_secret) == "198.51.100.4"
    wrong = _Req({"x-proxy-secret": "nope", "x-client-ip": "198.51.100.4",
                  "x-forwarded-for": "9.9.9.9"})
    assert client_ip(wrong) == "9.9.9.9"


def test_client_ip_falls_back_to_the_socket_peer() -> None:
    assert client_ip(_Req({})) == "10.0.0.9"


# --- rate limiter -----------------------------------------------------------


class _DeadRedis:
    def incr(self, key):  # noqa: ANN001
        raise RedisError("down")


def test_limiter_keeps_limiting_without_redis() -> None:
    limiter = RateLimiter("t-" + __name__, limit=2, window_seconds=60)
    dead = _DeadRedis()
    assert limiter.check(dead, "1.2.3.4").allowed
    assert limiter.check(dead, "1.2.3.4").allowed
    third = limiter.check(dead, "1.2.3.4")
    assert not third.allowed
    assert third.retry_after >= 1
    assert limiter.check(dead, "5.6.7.8").allowed, "windows are per address"


# --- origin check -----------------------------------------------------------


@pytest.fixture
def client() -> TestClient:
    app.dependency_overrides[get_redis] = lambda: InMemoryRedis()
    yield TestClient(app)
    app.dependency_overrides.pop(get_redis, None)


def test_cross_site_write_is_refused(client: TestClient) -> None:
    resp = client.post("/api/v1/auth/guest", headers={"Origin": "https://evil.example"})
    assert resp.status_code == 403


def test_same_site_write_is_allowed(client: TestClient) -> None:
    origin = get_settings().cors_origins_list[0]
    resp = client.post("/api/v1/auth/login", json={}, headers={"Origin": origin})
    assert resp.status_code == 422  # past the origin check, into validation


def test_cross_site_read_is_not_blocked(client: TestClient) -> None:
    resp = client.get("/api/v1/health", headers={"Origin": "https://evil.example"})
    assert resp.status_code == 200


# --- turnstile --------------------------------------------------------------


def test_turnstile_is_a_no_op_when_unconfigured(monkeypatch) -> None:
    monkeypatch.setattr(get_settings(), "turnstile_secret_key", None)
    assert turnstile.verify_turnstile(None) is True


def test_turnstile_requires_a_token_when_configured(monkeypatch) -> None:
    monkeypatch.setattr(get_settings(), "turnstile_secret_key", "sk")
    assert turnstile.verify_turnstile(None) is False
    assert turnstile.verify_turnstile("") is False


def test_turnstile_accepts_cloudflares_verdict(monkeypatch) -> None:
    monkeypatch.setattr(get_settings(), "turnstile_secret_key", "sk")

    class _Resp:
        def __init__(self, ok: bool) -> None:
            self._ok = ok

        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict:
            return {"success": self._ok}

    monkeypatch.setattr(turnstile.httpx, "post", lambda *a, **k: _Resp(True))
    assert turnstile.verify_turnstile("tok", "1.2.3.4") is True
    monkeypatch.setattr(turnstile.httpx, "post", lambda *a, **k: _Resp(False))
    assert turnstile.verify_turnstile("tok") is False


def test_signup_is_gated_by_turnstile_when_configured(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(get_settings(), "turnstile_secret_key", "sk")
    resp = client.post(
        "/api/v1/auth/signup", json={"email": "x@example.com", "password": "long-enough-1"}
    )
    assert resp.status_code == 403
    assert resp.json()["detail"]["challenge"] == "turnstile"


# --- forwarded chain: rightmost public entry wins ---------------------------


def test_client_ip_skips_the_balancers_internal_hops() -> None:
    # Render appends the client, then its own 10.x hop.
    assert client_ip(_Req({"x-forwarded-for": "93.184.216.34, 10.28.55.214"})) == "93.184.216.34"
    # A spoofed leftmost entry never wins over what the balancer appended.
    chain = "1.1.1.1, 93.184.216.34, 10.28.55.214"
    assert client_ip(_Req({"x-forwarded-for": chain})) == "93.184.216.34"
    # Garbage is skipped, not trusted.
    assert client_ip(_Req({"x-forwarded-for": "93.184.216.34, not-an-ip"})) == "93.184.216.34"
    # With nothing public in the chain, fall back to the last hop.
    assert client_ip(_Req({"x-forwarded-for": "10.0.0.1, 10.0.0.2"})) == "10.0.0.2"


# --- deep health reports whether the proxy secret matched -------------------


def test_deep_health_reports_proxy_trust(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(get_settings(), "proxy_shared_secret", "s3cret")

    assert client.get("/api/v1/health/deep").json()["proxy"] == "direct"
    wrong = client.get("/api/v1/health/deep", headers={"X-Proxy-Secret": "nope"})
    assert wrong.json()["proxy"] == "direct"
    right = client.get(
        "/api/v1/health/deep", headers={"X-Proxy-Secret": "s3cret", "X-Client-IP": "198.51.100.7"}
    )
    assert right.json()["proxy"] == "trusted"
    assert right.json()["client"] == "198.51.100.7"
