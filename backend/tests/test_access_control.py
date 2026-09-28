"""Authorization: who may call what, and whose records they may touch.

Three distinct properties are covered here, because they fail in different ways:

1. Authentication — protected routes reject anonymous callers. The browser
   gates these pages already, but a UI guard is a convenience, not a control.
2. Ownership — an authenticated user cannot reach another user's records by
   guessing an id (IDOR). The services take the owner from the token and must
   scope every read and write by it.
3. Field integrity — a client cannot set fields it doesn't own by smuggling
   them into a request body.
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.cache.redis_client import get_redis
from app.db.models.alert import Alert
from app.main import app
from app.services import alert_service
from app.services.market_data.fake_provider import FakeProvider
from app.services.market_data.registry import get_provider
from tests.conftest import InMemoryRedis, make_user

# --- 1. authentication -------------------------------------------------------

# Every route that reads market data, runs the model, or touches user records.
PROTECTED: list[tuple[str, str]] = [
    ("GET", "/api/v1/stocks/search?q=apple"),
    ("GET", "/api/v1/stocks/NVDA"),
    ("GET", "/api/v1/stocks/NVDA/quote"),
    ("GET", "/api/v1/stocks/NVDA/history"),
    ("GET", "/api/v1/stocks/NVDA/indicators"),
    ("GET", "/api/v1/stocks/NVDA/risk"),
    ("GET", "/api/v1/stocks/NVDA/sentiment"),
    ("POST", "/api/v1/predictions/NVDA"),
    ("GET", "/api/v1/predictions/NVDA/history"),
    ("GET", "/api/v1/watchlist"),
    ("POST", "/api/v1/watchlist/NVDA"),
    ("DELETE", "/api/v1/watchlist/NVDA"),
    ("GET", "/api/v1/alerts"),
    ("POST", "/api/v1/alerts"),
    ("GET", "/api/v1/alerts/events"),
    ("GET", "/api/v1/backtests"),
    ("POST", "/api/v1/backtests/NVDA"),
    ("GET", "/api/v1/auth/me"),
]

# Deliberately open: liveness probes and the model transparency page, which is
# public marketing content.
PUBLIC: list[str] = [
    "/api/v1/health",
    "/api/v1/health/deep",
    "/api/v1/models",
]

# Necessarily anonymous — you cannot hold a token before you have one. These are
# protected by rate limiting instead (see test_hardening.py).
PUBLIC_AUTH_FLOW: list[str] = [
    "/api/v1/auth/login",
    "/api/v1/auth/signup",
]


@pytest.mark.parametrize(("method", "path"), PROTECTED)
def test_protected_routes_reject_anonymous_callers(
    client: TestClient, method: str, path: str
) -> None:
    resp = client.request(method, path)
    assert resp.status_code in (401, 403), f"{method} {path} returned {resp.status_code}"


@pytest.mark.parametrize(("method", "path"), PROTECTED)
def test_protected_routes_reject_a_forged_token(
    client: TestClient, method: str, path: str
) -> None:
    resp = client.request(method, path, headers={"Authorization": "Bearer not.a.real.jwt"})
    assert resp.status_code == 401, f"{method} {path} returned {resp.status_code}"


@pytest.mark.parametrize("path", PUBLIC)
def test_public_routes_stay_public(client: TestClient, path: str) -> None:
    """Guards against over-correcting: locking these would break the landing
    page, the health check and the transparency page."""
    assert client.get(path).status_code == 200


@pytest.mark.parametrize("path", PUBLIC_AUTH_FLOW)
def test_auth_flow_is_reachable_without_a_token(client: TestClient, path: str) -> None:
    """These must not 401 — rejecting them for want of a token would be a
    chicken-and-egg lockout. An empty body is a 422, which proves we got past
    authentication and into validation."""
    resp = client.post(path, json={})
    assert resp.status_code == 422


def test_no_route_was_left_out_of_the_protected_list() -> None:
    """Fails when a new route ships without a decision about its auth posture."""
    known = {p.split("?")[0] for _, p in PROTECTED} | set(PUBLIC) | set(PUBLIC_AUTH_FLOW)
    live = {
        r.path
        for r in app.routes
        if getattr(r, "path", "").startswith("/api/v1")
    }
    # Compare by template shape: the lists above use concrete tickers/ids.
    templated = {p for p in live if "{" in p}
    concrete = live - templated
    assert concrete <= known, f"unclassified routes: {sorted(concrete - known)}"


# --- 2. ownership (IDOR) -----------------------------------------------------


class _SessionReturning:
    """A Session whose `get` hands back one preset row, whatever id is asked for.

    That is the worst case for an ownership check: the lookup always "succeeds",
    so the only thing standing between the caller and someone else's record is
    the user_id comparison under test.
    """

    def __init__(self, row: object) -> None:
        self.row = row
        self.deleted: list[object] = []
        self.committed = False

    def get(self, _model: object, _pk: object) -> object:
        return self.row

    def delete(self, row: object) -> None:
        self.deleted.append(row)

    def commit(self) -> None:
        self.committed = True

    def refresh(self, _row: object) -> None:
        pass


def _alert_owned_by(owner_id: uuid.UUID) -> Alert:
    return Alert(
        id=uuid.uuid4(),
        user_id=owner_id,
        ticker="NVDA",
        alert_type="price_above",
        threshold=100.0,
        active=True,
    )


def test_update_refuses_an_alert_owned_by_someone_else() -> None:
    victim, attacker = uuid.uuid4(), uuid.uuid4()
    alert = _alert_owned_by(victim)
    db = _SessionReturning(alert)

    result = alert_service.update_alert(db, attacker, alert.id, threshold=1.0, active=False)

    assert result is None, "another user's alert must not be updatable"
    assert alert.threshold == 100.0, "the record must be left untouched"
    assert alert.active is True
    assert not db.committed


def test_delete_refuses_an_alert_owned_by_someone_else() -> None:
    victim, attacker = uuid.uuid4(), uuid.uuid4()
    alert = _alert_owned_by(victim)
    db = _SessionReturning(alert)

    assert alert_service.delete_alert(db, attacker, alert.id) is False
    assert db.deleted == [], "the record must not be deleted"
    assert not db.committed


def test_the_owner_can_still_update_and_delete() -> None:
    """The ownership check must not be so strict that it locks out the owner."""
    owner = uuid.uuid4()
    alert = _alert_owned_by(owner)
    db = _SessionReturning(alert)

    assert alert_service.update_alert(db, owner, alert.id, threshold=42.0) is not None
    assert alert.threshold == 42.0
    assert alert_service.delete_alert(db, owner, alert.id) is True
    assert db.deleted == [alert]


def test_a_missing_record_is_a_miss_not_a_crash() -> None:
    db = _SessionReturning(None)
    assert alert_service.update_alert(db, uuid.uuid4(), uuid.uuid4(), threshold=1.0) is None
    assert alert_service.delete_alert(db, uuid.uuid4(), uuid.uuid4()) is False


# --- 3. field integrity ------------------------------------------------------


@pytest.fixture
def authed_client() -> TestClient:
    app.dependency_overrides[get_provider] = lambda: FakeProvider()
    app.dependency_overrides[get_current_user] = lambda: make_user()
    app.dependency_overrides[get_redis] = lambda: InMemoryRedis()
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_signup_rejects_an_unknown_field(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "tamper@example.com",
            "password": "a-good-password-123",
            "role": "admin",  # not a field we accept
        },
    )
    assert resp.status_code == 422


def test_login_rejects_an_unknown_field(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "a@b.com", "password": "whatever-123", "id": "00000000" * 4},
    )
    assert resp.status_code == 422


def test_alert_create_rejects_a_smuggled_owner(authed_client: TestClient) -> None:
    """user_id comes from the token; sending one must fail, not be ignored."""
    resp = authed_client.post(
        "/api/v1/alerts",
        json={
            "ticker": "NVDA",
            "alert_type": "price_above",
            "threshold": 1.0,
            "user_id": str(uuid.uuid4()),
        },
    )
    assert resp.status_code == 422


def test_alert_update_rejects_an_unknown_field(authed_client: TestClient) -> None:
    resp = authed_client.patch(
        f"/api/v1/alerts/{uuid.uuid4()}",
        json={"threshold": 5.0, "user_id": str(uuid.uuid4())},
    )
    assert resp.status_code == 422


def test_login_response_never_includes_the_password_hash(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "wrong-password-123"},
    )
    assert "password_hash" not in resp.text
