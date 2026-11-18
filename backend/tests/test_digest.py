"""The daily digest: written once, cached as a row, grounded in tool results.

The model is a scripted stand-in; what matters is what gets gathered for it,
that a day's digest is paid for once, and that the endpoints degrade to a
clear reason instead of an error when Stock-man is offline or out of budget.
"""

from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.api.v1 import stockman as stockman_api
from app.cache.redis_client import get_redis
from app.db.models.user import User
from app.db.session import SessionLocal, get_db, set_rls_user, system_session
from app.main import app
from app.services import portfolio_service, watchlist_service
from app.services.market_data.fake_provider import FakeProvider
from app.services.market_data.registry import get_provider
from app.services.stockman import budget, digest
from tests.conftest import InMemoryRedis

PROVIDER = FakeProvider()


class FakeClient:
    def __init__(self, text: str = "A quiet day for the account; nothing moved much.") -> None:
        self.text = text
        self.requests: list[dict] = []
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **kwargs: object) -> SimpleNamespace:
        self.requests.append(kwargs)
        return SimpleNamespace(
            content=[SimpleNamespace(type="text", text=self.text)],
            stop_reason="end_turn",
            usage=SimpleNamespace(input_tokens=900, output_tokens=150),
        )


@pytest.fixture
def user_id():
    db = system_session()
    user = User(is_guest=True)
    db.add(user)
    db.commit()
    uid = user.id
    db.close()
    yield uid
    db = system_session()
    db.query(User).filter(User.id == uid).delete(synchronize_session=False)
    db.commit()
    db.close()


@pytest.fixture
def db(user_id):
    session = SessionLocal()
    set_rls_user(session, user_id)
    yield session
    session.close()


def test_a_portfolio_digest_gathers_the_holdings_and_their_signals(db, user_id) -> None:
    redis = InMemoryRedis()
    portfolio_service.trade(db, redis, PROVIDER, user_id, "AAPL", "buy", Decimal("5"))
    portfolio_service.trade(db, redis, PROVIDER, user_id, "NVDA", "buy", Decimal("1"))
    client = FakeClient()

    out = digest.generate(db, redis, PROVIDER, client, user_id)

    assert out["available"] is True and out["mode"] == "portfolio"
    tools_used = {(s["tool"], s.get("ticker")) for s in out["sources"]}
    assert ("get_portfolio", None) in tools_used
    assert ("get_risk", "AAPL") in tools_used and ("get_sentiment", "NVDA") in tools_used
    prompt = client.requests[0]["messages"][0]["content"]
    assert "Write today's digest for this paper portfolio" in prompt
    assert '"risk:AAPL"' in prompt


def test_an_uninvested_account_gets_a_market_digest_from_the_watchlist(db, user_id) -> None:
    redis = InMemoryRedis()
    watchlist_service.add(db, user_id, "TSLA")
    client = FakeClient()

    out = digest.generate(db, redis, PROVIDER, client, user_id)

    assert out["mode"] == "market"
    assert {s.get("ticker") for s in out["sources"]} == {"TSLA"}
    assert "holds only cash" in client.requests[0]["messages"][0]["content"]


def test_the_second_read_of_the_day_is_the_cached_row(db, user_id) -> None:
    redis = InMemoryRedis()
    client = FakeClient()
    first = digest.generate(db, redis, PROVIDER, client, user_id)
    second = digest.generate(db, redis, PROVIDER, client, user_id)
    assert second == first
    assert len(client.requests) == 1
    assert digest.today(db, user_id) == first


def test_force_rewrites_todays_row_in_place(db, user_id) -> None:
    redis = InMemoryRedis()
    digest.generate(db, redis, PROVIDER, FakeClient("first"), user_id)
    out = digest.generate(db, redis, PROVIDER, FakeClient("second"), user_id, force=True)
    assert out["body"] == "second"
    assert digest.today(db, user_id)["body"] == "second"


def test_ungrounded_figures_are_recorded_with_the_digest(db, user_id) -> None:
    redis = InMemoryRedis()
    out = digest.generate(db, redis, PROVIDER, FakeClient("AAPL will reach $987.65."), user_id)
    assert out["grounding"]["unmatched"] == ["$987.65"]


def test_a_second_writer_backs_off_while_the_lock_is_held(db, user_id) -> None:
    redis = InMemoryRedis()
    redis.set(f"stockman:digest:lock:{user_id}:{digest._day()}", "1", nx=True)
    with pytest.raises(digest.DigestBusy):
        digest.generate(db, redis, PROVIDER, FakeClient(), user_id)


# --- the API --------------------------------------------------------------------


@pytest.fixture
def client(user_id, monkeypatch):
    def scoped_db():
        session = SessionLocal()
        set_rls_user(session, user_id)
        try:
            yield session
        finally:
            session.close()

    fake = FakeClient()
    app.dependency_overrides[get_db] = scoped_db
    app.dependency_overrides[get_current_user] = lambda: User(id=user_id, is_guest=True)
    app.dependency_overrides[get_provider] = lambda: PROVIDER
    app.dependency_overrides[get_redis] = lambda: InMemoryRedis()
    app.dependency_overrides[stockman_api.get_anthropic_client] = lambda: fake
    monkeypatch.setattr(stockman_api._settings, "anthropic_api_key", "test-key")
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_the_dashboard_read_writes_then_serves_the_digest(client: TestClient) -> None:
    first = client.get("/api/v1/stockman/digest").json()
    assert first["available"] is True
    assert "Not financial advice" in first["disclaimer"]
    second = client.get("/api/v1/stockman/digest").json()
    assert second["body"] == first["body"]
    assert second["generated_at"] == first["generated_at"]


def test_refresh_writes_a_new_one(client: TestClient) -> None:
    first = client.get("/api/v1/stockman/digest").json()
    fresh = client.post("/api/v1/stockman/digest/refresh").json()
    assert fresh["available"] is True
    assert fresh["generated_at"] >= first["generated_at"]


def test_offline_and_out_of_budget_are_reasons_not_errors(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(budget.get_settings(), "stockman_user_daily_tokens", 0)
    resting = client.get("/api/v1/stockman/digest").json()
    assert resting["available"] is False and "resting" in resting["reason"]

    monkeypatch.setattr(stockman_api._settings, "anthropic_api_key", None)
    offline = client.get("/api/v1/stockman/digest").json()
    assert offline["available"] is False and "offline" in offline["reason"]
