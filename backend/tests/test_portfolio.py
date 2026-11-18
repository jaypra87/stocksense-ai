"""Paper trading: fills, cost basis, P&L, and the limits of the account.

Runs against the real Postgres like test_rls.py, because the behaviour worth
proving (the row lock on the account, ownership reaching positions through
the portfolio, the guest merge) lives in the database rather than in Python.
"""

import uuid
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.api.deps import get_current_user
from app.cache.redis_client import get_redis
from app.db.models.portfolio import Portfolio, Position
from app.db.models.user import User
from app.db.session import SessionLocal, get_db, set_rls_user, system_session
from app.main import app
from app.services import auth_service, portfolio_service, stock_service
from app.services.market_data.fake_provider import FakeProvider
from app.services.market_data.registry import get_provider
from app.services.portfolio_service import InsufficientFundsError, InsufficientSharesError
from tests.conftest import InMemoryRedis

PROVIDER = FakeProvider()


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


@pytest.fixture
def redis():
    return InMemoryRedis()


def price_of(redis, ticker: str) -> Decimal:
    return Decimal(str(stock_service.get_quote(redis, PROVIDER, ticker)["price"]))


def buy(db, redis, user_id, ticker, **size):
    return portfolio_service.trade(db, redis, PROVIDER, user_id, ticker, "buy", **size)


def sell(db, redis, user_id, ticker, **size):
    return portfolio_service.trade(db, redis, PROVIDER, user_id, ticker, "sell", **size)


# --- the account ---------------------------------------------------------------


def test_a_fresh_account_holds_the_starting_cash_and_nothing_else(db, redis, user_id) -> None:
    summary = portfolio_service.summary(db, redis, PROVIDER, user_id)
    assert summary["cash"] == 100_000
    assert summary["equity"] == 100_000
    assert summary["positions"] == []
    assert summary["total_return"] == 0
    assert (
        "Not financial advice" in summary["disclaimer"]
        or "not financial advice" in summary["disclaimer"]
    )


def test_buying_debits_cash_and_opens_a_position_at_the_fill_price(db, redis, user_id) -> None:
    price = price_of(redis, "AAPL")
    fill = buy(db, redis, user_id, "aapl", quantity=Decimal("10"))

    assert fill["ticker"] == "AAPL"
    assert Decimal(str(fill["price"])) == price
    summary = portfolio_service.summary(db, redis, PROVIDER, user_id)
    assert Decimal(str(summary["cash"])) == Decimal("100000") - price * 10
    (position,) = summary["positions"]
    assert position["quantity"] == 10
    assert Decimal(str(position["avg_cost"])) == price
    assert position["unrealized_pnl"] == 0


def test_a_second_buy_averages_the_cost_basis(db, redis, user_id) -> None:
    buy(db, redis, user_id, "AAPL", quantity=Decimal("10"))
    # Nudge the entry price so the average is observable.
    position = db.execute(select(Position)).scalar_one()
    position.avg_cost = Decimal("100")
    db.commit()
    price = price_of(redis, "AAPL")

    buy(db, redis, user_id, "AAPL", quantity=Decimal("10"))

    position = db.execute(select(Position)).scalar_one()
    assert position.quantity == 20
    assert position.avg_cost == ((Decimal("100") * 10 + price * 10) / 20).quantize(
        Decimal("0.0001")
    )


def test_sizing_in_money_buys_fractional_shares(db, redis, user_id) -> None:
    price = price_of(redis, "NVDA")
    fill = buy(db, redis, user_id, "NVDA", amount=Decimal("1000"))

    quantity = Decimal(str(fill["quantity"]))
    assert quantity == (Decimal("1000") / price).quantize(
        Decimal("0.000001"), rounding="ROUND_DOWN"
    )
    assert quantity * price <= 1000


def test_you_cannot_spend_more_than_you_have(db, redis, user_id) -> None:
    with pytest.raises(InsufficientFundsError):
        buy(db, redis, user_id, "AAPL", amount=Decimal("100001"))
    summary = portfolio_service.summary(db, redis, PROVIDER, user_id)
    assert summary["cash"] == 100_000
    assert summary["positions"] == []


def test_selling_realizes_the_gain_against_the_average_cost(db, redis, user_id) -> None:
    buy(db, redis, user_id, "AAPL", quantity=Decimal("10"))
    position = db.execute(select(Position)).scalar_one()
    position.avg_cost = Decimal("50")
    db.commit()
    price = price_of(redis, "AAPL")

    fill = sell(db, redis, user_id, "AAPL", quantity=Decimal("4"))

    assert Decimal(str(fill["realized_pnl"])) == ((price - 50) * 4).quantize(Decimal("0.0001"))
    position = db.execute(select(Position)).scalar_one()
    assert position.quantity == 6
    summary = portfolio_service.summary(db, redis, PROVIDER, user_id)
    assert Decimal(str(summary["realized_pnl"])) == Decimal(str(fill["realized_pnl"]))


def test_selling_the_whole_lot_closes_the_position_even_when_rounded(db, redis, user_id) -> None:
    buy(db, redis, user_id, "NVDA", amount=Decimal("333.33"))
    held = db.execute(select(Position)).scalar_one().quantity

    sell(db, redis, user_id, "NVDA", quantity=held + Decimal("0.000001"))

    assert db.execute(select(Position)).scalar_one_or_none() is None


def test_you_cannot_sell_what_you_do_not_hold(db, redis, user_id) -> None:
    with pytest.raises(InsufficientSharesError):
        sell(db, redis, user_id, "AAPL", quantity=Decimal("1"))
    buy(db, redis, user_id, "AAPL", quantity=Decimal("2"))
    with pytest.raises(InsufficientSharesError):
        sell(db, redis, user_id, "AAPL", quantity=Decimal("3"))


def test_dust_orders_are_refused(db, redis, user_id) -> None:
    with pytest.raises(portfolio_service.TradeError):
        buy(db, redis, user_id, "AAPL", amount=Decimal("0.00001"))


def test_reset_restores_the_starting_balance_and_clears_the_ledger(db, redis, user_id) -> None:
    buy(db, redis, user_id, "AAPL", quantity=Decimal("3"))
    sell(db, redis, user_id, "AAPL", quantity=Decimal("1"))

    portfolio_service.reset(db, user_id)

    summary = portfolio_service.summary(db, redis, PROVIDER, user_id)
    assert summary["cash"] == 100_000
    assert summary["positions"] == []
    assert summary["realized_pnl"] == 0
    assert summary["reset_at"] is not None
    assert portfolio_service.list_trades(db, user_id) == []


def test_weights_add_up_across_positions(db, redis, user_id) -> None:
    buy(db, redis, user_id, "AAPL", amount=Decimal("25000"))
    buy(db, redis, user_id, "NVDA", amount=Decimal("25000"))

    summary = portfolio_service.summary(db, redis, PROVIDER, user_id)

    invested = sum(p["weight"] for p in summary["positions"])
    cash_weight = summary["cash"] / summary["equity"] * 100
    assert invested + cash_weight == pytest.approx(100, abs=0.05)


# --- ownership ------------------------------------------------------------------


def test_another_user_cannot_see_the_positions_or_the_ledger(db, redis, user_id) -> None:
    buy(db, redis, user_id, "AAPL", quantity=Decimal("1"))
    other = system_session()
    stranger = User(is_guest=True)
    other.add(stranger)
    other.commit()
    try:
        peek = SessionLocal()
        set_rls_user(peek, stranger.id)
        assert peek.execute(select(Position)).scalars().all() == []
        assert peek.execute(select(Portfolio)).scalars().all() == []
        peek.close()
    finally:
        other.delete(stranger)
        other.commit()
        other.close()


def test_a_guest_portfolio_follows_the_guest_into_an_empty_account(redis, user_id) -> None:
    db = system_session()
    guest = db.get(User, user_id)
    account = User(is_guest=False)
    db.add(account)
    db.commit()
    buy(db, redis, user_id, "AAPL", quantity=Decimal("2"))

    auth_service.merge_guest_into(db, guest, account)

    moved = db.execute(select(Portfolio).where(Portfolio.user_id == account.id)).scalar_one()
    assert db.execute(select(Position).where(Position.portfolio_id == moved.id)).scalar_one()
    db.delete(account)
    db.commit()
    db.close()


def test_an_account_with_trades_keeps_its_own_portfolio_on_merge(redis, user_id) -> None:
    db = system_session()
    guest = db.get(User, user_id)
    account = User(is_guest=False)
    db.add(account)
    db.commit()
    buy(db, redis, user_id, "AAPL", quantity=Decimal("2"))
    buy(db, redis, account.id, "NVDA", quantity=Decimal("1"))

    auth_service.merge_guest_into(db, guest, account)

    kept = db.execute(select(Portfolio).where(Portfolio.user_id == account.id)).scalar_one()
    tickers = (
        db.execute(select(Position.ticker).where(Position.portfolio_id == kept.id)).scalars().all()
    )
    assert tickers == ["NVDA"]
    db.delete(account)
    db.commit()
    db.close()


# --- the API --------------------------------------------------------------------


@pytest.fixture
def client(user_id):
    def scoped_db():
        session = SessionLocal()
        set_rls_user(session, user_id)
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = scoped_db
    app.dependency_overrides[get_current_user] = lambda: User(id=user_id, is_guest=True)
    app.dependency_overrides[get_provider] = lambda: PROVIDER
    app.dependency_overrides[get_redis] = lambda: InMemoryRedis()
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_place_and_read_back_a_trade(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/portfolio/trades", json={"ticker": "aapl", "side": "buy", "amount": "500"}
    )
    assert resp.status_code == 201, resp.text
    fill = resp.json()
    assert fill["side"] == "buy"
    assert fill["total"] <= 500

    portfolio = client.get("/api/v1/portfolio").json()
    assert [p["ticker"] for p in portfolio["positions"]] == ["AAPL"]
    assert portfolio["cash"] == pytest.approx(100_000 - fill["total"], abs=0.01)
    assert client.get("/api/v1/portfolio/trades").json()[0]["id"] == fill["id"]


def test_an_unaffordable_order_is_a_409_with_a_reason(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/portfolio/trades", json={"ticker": "AAPL", "side": "buy", "amount": "999999"}
    )
    assert resp.status_code == 409
    assert "cash" in resp.json()["detail"]


def test_an_order_must_be_sized_one_way(client: TestClient) -> None:
    both = {"ticker": "AAPL", "side": "buy", "quantity": "1", "amount": "100"}
    assert client.post("/api/v1/portfolio/trades", json=both).status_code == 422
    neither = {"ticker": "AAPL", "side": "buy"}
    assert client.post("/api/v1/portfolio/trades", json=neither).status_code == 422


def test_a_smuggled_owner_is_rejected(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/portfolio/trades",
        json={"ticker": "AAPL", "side": "buy", "amount": "10", "user_id": str(uuid.uuid4())},
    )
    assert resp.status_code == 422


def test_a_malformed_ticker_is_a_422(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/portfolio/trades", json={"ticker": "not a ticker", "side": "buy", "amount": "10"}
    )
    assert resp.status_code == 422


def test_reset_returns_the_fresh_account(client: TestClient) -> None:
    client.post("/api/v1/portfolio/trades", json={"ticker": "AAPL", "side": "buy", "amount": "10"})
    resp = client.post("/api/v1/portfolio/reset")
    assert resp.status_code == 200
    assert resp.json()["positions"] == []
    assert resp.json()["cash"] == 100_000
