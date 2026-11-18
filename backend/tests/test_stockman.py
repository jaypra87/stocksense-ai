"""Stock-man: the grounding check, the tools, the turn loop and the API.

The model is replaced by a scripted client everywhere. What is under test is
the machinery around it: that numbers in an answer trace back to tool
results, that a tool round is replayed correctly, that an ungrounded answer
is retried once, and that the endpoints respect ownership and the budget.
"""

import copy
import json
import uuid
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
from app.services import portfolio_service
from app.services.market_data.fake_provider import FakeProvider
from app.services.market_data.registry import get_provider
from app.services.stockman import agent, budget, grounding, tools
from app.services.stockman.prompts import REFUSED
from app.services.stockman.tools import ToolContext, ToolError
from tests.conftest import InMemoryRedis

PROVIDER = FakeProvider()

# --- grounding ------------------------------------------------------------------


def test_figures_from_tool_results_pass_in_the_forms_a_model_quotes_them() -> None:
    results = [{"price": 151.86, "confidence": 0.6234, "change_percent": -0.48}]
    answer = "AAPL is at $151.86 (about $152), down 0.5%, with 62% confidence."
    assert grounding.check(answer, results) == {"checked": 4, "unmatched": []}


def test_an_invented_figure_is_flagged() -> None:
    results = [{"price": 151.86}]
    check = grounding.check("AAPL trades at $151.86 and should hit $210.50 soon.", results)
    assert check["unmatched"] == ["$210.50"]


def test_counts_years_horizons_and_the_users_own_numbers_are_not_flagged() -> None:
    check = grounding.check(
        "Over 7 days, across 3 headlines in 2026 and the 52-week range, $500 fits your plan.",
        [{"price": 10.0}],
        user_text="I have $500 to invest",
    )
    assert check["unmatched"] == []


def test_a_figure_far_from_any_result_does_not_match_by_tolerance() -> None:
    assert grounding.check("$160.00", [{"price": 151.86}])["unmatched"] == ["$160.00"]


# --- tools ----------------------------------------------------------------------


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
def ctx(user_id):
    session = SessionLocal()
    set_rls_user(session, user_id)
    yield ToolContext(db=session, redis=InMemoryRedis(), provider=PROVIDER, user_id=user_id)
    session.close()


def test_quote_tool_returns_the_trimmed_snapshot(ctx) -> None:
    out = tools.run(ctx, "get_quote", {"ticker": "aapl"})
    assert out["ticker"] == "AAPL"
    assert out["price"] > 0
    assert "as_of" in out and "series" not in out


def test_unknown_ticker_is_a_tool_error_not_a_crash(ctx) -> None:
    with pytest.raises(ToolError, match="Unknown ticker"):
        tools.run(ctx, "get_quote", {"ticker": "not a ticker"})


def test_portfolio_tool_sees_the_users_positions(ctx) -> None:
    portfolio_service.trade(ctx.db, ctx.redis, PROVIDER, ctx.user_id, "NVDA", "buy", Decimal("2"))
    out = tools.run(ctx, "get_portfolio", {})
    assert [p["ticker"] for p in out["positions"]] == ["NVDA"]
    assert out["cash"] < 100_000


def test_a_trade_proposal_is_priced_but_never_executed(ctx) -> None:
    out = tools.run(
        ctx,
        "propose_paper_trade",
        {"ticker": "AAPL", "side": "buy", "quantity": None, "amount": 1000, "rationale": "test"},
    )
    assert out["proposal"] is True
    assert out["estimated_total"] <= 1000
    assert out["cash_available"] == 100_000
    assert tools.run(ctx, "get_portfolio", {})["positions"] == []


def test_a_proposal_must_be_sized_one_way(ctx) -> None:
    with pytest.raises(ToolError):
        tools.run(
            ctx,
            "propose_paper_trade",
            {"ticker": "AAPL", "side": "buy", "quantity": 1, "amount": 100, "rationale": "x"},
        )


def test_every_definition_has_a_handler_and_a_strict_schema() -> None:
    names = {t["name"] for t in tools.TOOL_DEFINITIONS}
    assert names == set(tools._HANDLERS)
    for t in tools.TOOL_DEFINITIONS:
        assert t["strict"] is True
        assert t["input_schema"]["additionalProperties"] is False


# --- the turn loop --------------------------------------------------------------


class _Block(SimpleNamespace):
    def model_dump(self, **_: object) -> dict:
        return dict(vars(self))


def text(t: str) -> _Block:
    return _Block(type="text", text=t)


def tool_use(name: str, **args: object) -> _Block:
    return _Block(type="tool_use", id=f"toolu_{name}", name=name, input=args)


class _Stream:
    def __init__(self, blocks: list[_Block], stop_reason: str) -> None:
        self.blocks, self.stop_reason = blocks, stop_reason

    def __enter__(self):
        return self

    def __exit__(self, *exc: object) -> None:
        pass

    def __iter__(self):
        for b in self.blocks:
            if b.type == "text":
                yield SimpleNamespace(type="text", text=b.text)

    def get_final_message(self):
        return SimpleNamespace(
            content=self.blocks,
            stop_reason=self.stop_reason,
            usage=SimpleNamespace(input_tokens=100, output_tokens=20),
        )


class FakeClient:
    """Plays back scripted turns and records every request it was sent."""

    def __init__(self, turns: list[tuple[list[_Block], str]]) -> None:
        self.turns = list(turns)
        self.requests: list[dict] = []
        self.messages = SimpleNamespace(stream=self._stream)

    def _stream(self, **kwargs: object) -> _Stream:
        self.requests.append(copy.deepcopy(kwargs))
        if not self.turns:
            raise AssertionError("more model calls than scripted turns")
        blocks, stop = self.turns.pop(0)
        return _Stream(blocks, stop)


def run(client: FakeClient, ctx: ToolContext, question: str) -> list[tuple[str, dict]]:
    return list(agent.run_turn(client, ctx, [], question))


def test_a_tool_round_is_executed_and_replayed_before_the_answer(ctx) -> None:
    client = FakeClient(
        [
            ([text("Let me check."), tool_use("get_quote", ticker="AAPL")], "tool_use"),
            ([text("AAPL is at $PRICE.")], "end_turn"),
        ]
    )
    events = run(client, ctx, "How is AAPL doing?")
    kinds = [k for k, _ in events]
    assert kinds[:1] == ["text_delta"]
    assert "tool_call" in kinds and "tool_result" in kinds
    assert kinds[-1] == "done"

    # The second request carries the assistant's tool_use and our tool_result.
    replayed = client.requests[1]["messages"]
    assert replayed[-2]["role"] == "assistant"
    assert replayed[-1]["content"][0]["type"] == "tool_result"
    assert "price" in json.loads(replayed[-1]["content"][0]["content"])

    done = events[-1][1]
    assert [t["role"] for t in done["transcript"]] == ["assistant", "user", "assistant"]
    assert done["usage"] == {"input_tokens": 200, "output_tokens": 40, "cache_read_input_tokens": 0}


def test_an_ungrounded_answer_is_retried_once_with_a_review_nudge(ctx) -> None:
    client = FakeClient(
        [
            ([tool_use("get_quote", ticker="AAPL")], "tool_use"),
            ([text("AAPL will hit $999.99 next week.")], "end_turn"),
            ([text("I can't give a target; the quote is what the tool returned.")], "end_turn"),
        ]
    )
    events = run(client, ctx, "Where is AAPL going?")
    kinds = [k for k, _ in events]
    assert kinds.count("text_reset") == 1
    nudge = client.requests[2]["messages"][-1]
    assert nudge["role"] == "system" and "$999.99" in nudge["content"]

    done = events[-1][1]
    assert done["grounding"]["unmatched"] == []
    assert done["answer"].startswith("I can't give a target")
    # The superseded answer is not part of what gets saved.
    assert all("$999.99" not in json.dumps(t) for t in done["transcript"])


def test_a_refusal_becomes_a_polite_fixed_reply(ctx) -> None:
    client = FakeClient([([text("partial")], "refusal")])
    events = run(client, ctx, "something off-limits")
    assert events[-1][1]["answer"] == REFUSED
    assert ("text_reset", {}) in events


def test_the_final_round_is_forced_to_answer_without_tools(ctx, monkeypatch) -> None:
    monkeypatch.setattr(agent.get_settings(), "stockman_max_tool_rounds", 2)
    client = FakeClient(
        [
            ([tool_use("get_quote", ticker="AAPL")], "tool_use"),
            ([text("Here is what I have.")], "end_turn"),
        ]
    )
    events = run(client, ctx, "AAPL?")
    assert client.requests[0]["tool_choice"] == {"type": "auto"}
    assert client.requests[1]["tool_choice"] == {"type": "none"}
    assert events[-1][1]["rounds"] == 2


def test_a_failing_tool_is_reported_to_the_model_not_raised(ctx) -> None:
    client = FakeClient(
        [
            ([tool_use("get_quote", ticker="not a ticker")], "tool_use"),
            ([text("That ticker doesn't exist.")], "end_turn"),
        ]
    )
    events = run(client, ctx, "Quote for nonsense?")
    result = client.requests[1]["messages"][-1]["content"][0]
    assert result["is_error"] is True and "Unknown ticker" in result["content"]
    assert [d for k, d in events if k == "tool_result"][0]["ok"] is False


# --- budget ---------------------------------------------------------------------


def test_budget_charges_count_toward_both_scopes_and_block_at_the_cap(monkeypatch) -> None:
    redis = InMemoryRedis()
    uid = uuid.uuid4()
    monkeypatch.setattr(budget.get_settings(), "stockman_user_daily_tokens", 1000)
    budget.charge(redis, uid, 600)
    budget.check(redis, uid)
    budget.charge(redis, uid, 500)
    assert budget.usage(redis, uid) == (1100, 1100)
    with pytest.raises(budget.BudgetExceeded):
        budget.check(redis, uid)


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

    redis = InMemoryRedis()
    app.dependency_overrides[get_db] = scoped_db
    app.dependency_overrides[get_current_user] = lambda: User(id=user_id, is_guest=True)
    app.dependency_overrides[get_provider] = lambda: PROVIDER
    app.dependency_overrides[get_redis] = lambda: redis
    monkeypatch.setattr(stockman_api._settings, "anthropic_api_key", "test-key")
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_status_reports_the_model_and_the_budget(client: TestClient) -> None:
    body = client.get("/api/v1/stockman/status").json()
    assert body["enabled"] is True
    assert body["budget"]["used"] == 0
    assert "Not financial advice" in body["disclaimer"]


def test_conversations_are_created_listed_and_deleted(client: TestClient) -> None:
    created = client.post("/api/v1/stockman/conversations", json={}).json()
    assert created["title"] == "New conversation"
    assert [c["id"] for c in client.get("/api/v1/stockman/conversations").json()] == [created["id"]]
    assert client.delete(f"/api/v1/stockman/conversations/{created['id']}").status_code == 204
    assert client.get(f"/api/v1/stockman/conversations/{created['id']}").status_code == 404


def test_someone_elses_conversation_is_a_404(client: TestClient) -> None:
    db = system_session()
    stranger = User(is_guest=True)
    db.add(stranger)
    db.commit()
    from app.db.models.conversation import Conversation

    theirs = Conversation(user_id=stranger.id, title="private")
    db.add(theirs)
    db.commit()
    try:
        assert client.get(f"/api/v1/stockman/conversations/{theirs.id}").status_code == 404
        resp = client.post(
            f"/api/v1/stockman/conversations/{theirs.id}/messages", json={"content": "hi"}
        )
        assert resp.status_code == 404
    finally:
        db.delete(stranger)
        db.commit()
        db.close()


def test_sending_without_a_key_is_a_503(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(stockman_api._settings, "anthropic_api_key", None)
    cid = client.post("/api/v1/stockman/conversations", json={}).json()["id"]
    resp = client.post(f"/api/v1/stockman/conversations/{cid}/messages", json={"content": "hi"})
    assert resp.status_code == 503
    assert "offline" in resp.json()["detail"]


def test_a_turn_streams_events_and_is_persisted(client: TestClient) -> None:
    fake = FakeClient(
        [
            ([tool_use("get_quote", ticker="AAPL")], "tool_use"),
            ([text("AAPL is trading at the quoted price.")], "end_turn"),
        ]
    )
    app.dependency_overrides[stockman_api.get_anthropic_client] = lambda: fake
    cid = client.post("/api/v1/stockman/conversations", json={}).json()["id"]

    resp = client.post(
        f"/api/v1/stockman/conversations/{cid}/messages", json={"content": "How is AAPL?"}
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")
    events = [
        line.split(": ", 1)[1] for line in resp.text.splitlines() if line.startswith("event: ")
    ]
    assert events[0] == "tool_call" and events[-1] == "done"

    saved = client.get(f"/api/v1/stockman/conversations/{cid}").json()
    assert saved["title"] == "How is AAPL?"
    assert [m["role"] for m in saved["messages"]] == ["user", "assistant", "user", "assistant"]
    assert saved["messages"][2]["content"][0]["type"] == "tool_result"
    assert client.get("/api/v1/stockman/status").json()["budget"]["used"] == 240


def test_an_exhausted_budget_is_a_429_with_a_friendly_reason(
    client: TestClient, monkeypatch
) -> None:
    monkeypatch.setattr(budget.get_settings(), "stockman_user_daily_tokens", 10)
    redis = app.dependency_overrides[get_redis]()
    budget.charge(redis, app.dependency_overrides[get_current_user]().id, 10)
    cid = client.post("/api/v1/stockman/conversations", json={}).json()["id"]
    resp = client.post(f"/api/v1/stockman/conversations/{cid}/messages", json={"content": "hi"})
    assert resp.status_code == 429
    assert "resting" in resp.json()["detail"]


def test_a_smuggled_field_on_a_message_is_rejected(client: TestClient) -> None:
    cid = client.post("/api/v1/stockman/conversations", json={}).json()["id"]
    resp = client.post(
        f"/api/v1/stockman/conversations/{cid}/messages",
        json={"content": "hi", "role": "system"},
    )
    assert resp.status_code == 422
