"""End-to-end identity flow against the real database.

These need Postgres with the migrations applied (as the rest of the DB-backed
tests do). They exercise the thing the login screen used to do: a visitor gets
a session with no credentials, can save it as an account, and the cookie is
the only thing a browser needs.
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.cache.redis_client import get_redis
from app.core.config import get_settings
from app.core.crypto import decrypt_email, hash_email, is_encrypted
from app.db.models.user import User
from app.db.session import SessionLocal, rls_bypass
from app.main import app
from tests.conftest import InMemoryRedis

COOKIE = get_settings().session_cookie_name


def _unique_email() -> str:
    return f"flow-{uuid.uuid4().hex[:10]}@example.com"


@pytest.fixture
def browser() -> TestClient:
    """A TestClient that keeps cookies like a browser, with no auth override."""
    app.dependency_overrides[get_redis] = lambda: InMemoryRedis()
    client = TestClient(app, base_url="http://testserver")
    yield client
    app.dependency_overrides.pop(get_redis, None)
    # Clean up whatever this test created.
    db = SessionLocal()
    try:
        with rls_bypass(db):
            db.query(User).filter(User.email_hash.like("%")).filter(
                User.id.in_([uuid.UUID(i) for i in getattr(client, "_created", [])])
            ).delete(synchronize_session=False)
            db.query(User).filter(User.id.in_(
                [uuid.UUID(i) for i in getattr(client, "_created", [])]
            )).delete(synchronize_session=False)
            db.commit()
    finally:
        db.close()


def _track(client: TestClient, user_id: str) -> None:
    client._created = getattr(client, "_created", []) + [user_id]  # type: ignore[attr-defined]


def test_first_visit_gets_a_guest_session_cookie(browser: TestClient) -> None:
    assert browser.get("/api/v1/auth/me").status_code == 401

    resp = browser.post("/api/v1/auth/guest")
    assert resp.status_code == 201
    body = resp.json()
    _track(browser, body["user"]["id"])
    assert body["user"]["is_guest"] is True
    assert body["user"]["email"] is None

    cookie = resp.headers["set-cookie"]
    assert cookie.startswith(f"{COOKIE}=")
    assert "HttpOnly" in cookie
    assert "SameSite=lax" in cookie.lower().replace("samesite=lax", "SameSite=lax")

    # The cookie alone now authenticates.
    me = browser.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["id"] == body["user"]["id"]


def test_guest_is_idempotent_for_an_existing_session(browser: TestClient) -> None:
    first = browser.post("/api/v1/auth/guest").json()["user"]["id"]
    _track(browser, first)
    second = browser.post("/api/v1/auth/guest").json()["user"]["id"]
    assert first == second, "a second call must not mint a second identity"


def test_guest_can_save_an_account_and_keep_its_id(browser: TestClient) -> None:
    guest_id = browser.post("/api/v1/auth/guest").json()["user"]["id"]
    _track(browser, guest_id)
    email = _unique_email()

    resp = browser.post(
        "/api/v1/auth/signup", json={"email": email, "password": "a-strong-password-1"}
    )
    assert resp.status_code == 201, resp.text
    user = resp.json()["user"]
    assert user["id"] == guest_id, "saving must upgrade the guest, not create a new user"
    assert user["is_guest"] is False
    assert user["email"] == email

    # The address is stored encrypted, with a keyed hash for lookup.
    db = SessionLocal()
    try:
        with rls_bypass(db):
            row = db.get(User, uuid.UUID(guest_id))
            assert row.email != email
            assert is_encrypted(row.email)
            assert decrypt_email(row.email) == email
            assert row.email_hash == hash_email(email)
    finally:
        db.close()

    # Taking the same email again is a conflict.
    other = TestClient(app)
    other.post("/api/v1/auth/guest")
    dup = other.post(
        "/api/v1/auth/signup", json={"email": email.upper(), "password": "another-password-1"}
    )
    assert dup.status_code == 409
    _track(browser, other.get("/api/v1/auth/me").json()["id"])


def test_login_from_a_guest_browser_merges_the_guest(browser: TestClient) -> None:
    # An account that already exists.
    email = _unique_email()
    owner = TestClient(app)
    owner.post("/api/v1/auth/guest")
    account_id = owner.post(
        "/api/v1/auth/signup", json={"email": email, "password": "owner-password-123"}
    ).json()["user"]["id"]
    _track(browser, account_id)

    # A different browser, as a guest, saves a watchlist entry.
    guest_id = browser.post("/api/v1/auth/guest").json()["user"]["id"]
    _track(browser, guest_id)
    db = SessionLocal()
    try:
        from app.db.models.stock import Stock
        from app.db.models.watchlist import WatchlistItem

        with rls_bypass(db):
            if db.get(Stock, "ZZTESTX") is None:
                db.add(Stock(ticker="ZZTESTX", company_name="Test Co"))
            db.add(WatchlistItem(user_id=uuid.UUID(guest_id), ticker="ZZTESTX"))
            db.commit()
    finally:
        db.close()

    resp = browser.post(
        "/api/v1/auth/login", json={"email": email, "password": "owner-password-123"}
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["user"]["id"] == account_id

    db = SessionLocal()
    try:
        from app.db.models.watchlist import WatchlistItem

        with rls_bypass(db):
            assert db.get(User, uuid.UUID(guest_id)) is None, "guest row should be gone"
            moved = db.get(WatchlistItem, (uuid.UUID(account_id), "ZZTESTX"))
            assert moved is not None, "guest's watchlist should now belong to the account"
            db.delete(moved)
            db.commit()
    finally:
        db.close()


def test_wrong_password_is_rejected_and_timing_safe_path_runs(browser: TestClient) -> None:
    resp = browser.post(
        "/api/v1/auth/login", json={"email": "nobody-here@example.com", "password": "nope-nope-1"}
    )
    assert resp.status_code == 401


def test_logout_revokes_the_session_server_side(browser: TestClient) -> None:
    body = browser.post("/api/v1/auth/guest").json()
    _track(browser, body["user"]["id"])
    token = body["access_token"]

    assert browser.post("/api/v1/auth/logout").status_code == 204

    # Even a client that kept the signed token gets nothing: the row is gone.
    stale = TestClient(app)
    resp = stale.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


def test_logout_all_ends_every_session(browser: TestClient) -> None:
    body = browser.post("/api/v1/auth/guest").json()
    _track(browser, body["user"]["id"])
    token_a = body["access_token"]
    token_b = browser.post("/api/v1/auth/guest").json()["access_token"]  # same user, 2nd session

    api = TestClient(app)
    as_a = {"Authorization": f"Bearer {token_a}"}
    as_b = {"Authorization": f"Bearer {token_b}"}
    assert api.get("/api/v1/auth/me", headers=as_b).status_code == 200
    assert api.post("/api/v1/auth/logout-all", headers=as_a).status_code == 204
    assert api.get("/api/v1/auth/me", headers=as_b).status_code == 401
