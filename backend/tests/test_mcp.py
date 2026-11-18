"""The MCP server: Stock-man's tools for outside assistants.

Spoken to the way a client would, as JSON-RPC over the streamable HTTP
transport, with the app's session token as the bearer credential.
"""

import json

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.core.security import create_session_token
from app.db.models.user import User
from app.db.session import SessionLocal, get_db, set_rls_user, system_session
from app.main import app
from app.mcp import server as mcp_server
from app.services import auth_service
from app.services.market_data.fake_provider import FakeProvider
from app.services.stockman.tools import TOOL_DEFINITIONS
from tests.conftest import InMemoryRedis

HEADERS = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}


@pytest.fixture
def account():
    db = system_session()
    user = User(is_guest=True)
    db.add(user)
    db.commit()
    session = auth_service.create_session(db, user, "test")
    token = create_session_token(user.id, session.id, session.expires_at)
    uid = user.id
    db.close()
    yield uid, token
    db = system_session()
    db.query(User).filter(User.id == uid).delete(synchronize_session=False)
    db.commit()
    db.close()


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(mcp_server, "get_provider", lambda: FakeProvider())
    monkeypatch.setattr(mcp_server, "get_redis", lambda: InMemoryRedis())
    # The context manager runs the app lifespan, which starts the transport.
    with TestClient(app) as c:
        yield c


def rpc(client: TestClient, token: str | None, method: str, params: dict | None = None):
    headers = dict(HEADERS)
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}
    return client.post("/mcp", json=body, headers=headers)


def test_no_token_is_turned_away_before_the_protocol(client: TestClient) -> None:
    resp = rpc(client, None, "tools/list")
    assert resp.status_code == 401
    assert resp.headers["www-authenticate"] == "Bearer"


def test_a_forged_token_is_turned_away(client: TestClient) -> None:
    assert rpc(client, "not.a.real.jwt", "tools/list").status_code == 401


def test_the_bare_path_is_served_without_a_redirect(client: TestClient, account) -> None:
    _, token = account
    headers = {**HEADERS, "Authorization": f"Bearer {token}"}
    body = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
    resp = client.post("/mcp", json=body, headers=headers, follow_redirects=False)
    assert resp.status_code == 200, resp.text


def test_every_stockman_tool_is_listed(client: TestClient, account) -> None:
    _, token = account
    resp = rpc(client, token, "tools/list")
    assert resp.status_code == 200, resp.text
    listed = resp.json()["result"]["tools"]
    assert {t["name"] for t in listed} == {t["name"] for t in TOOL_DEFINITIONS}
    quote = next(t for t in listed if t["name"] == "get_quote")
    assert quote["inputSchema"]["required"] == ["ticker"]


def test_a_tool_call_runs_as_the_token_holder(client: TestClient, account) -> None:
    _, token = account
    resp = rpc(client, token, "tools/call", {"name": "get_portfolio", "arguments": {}})
    assert resp.status_code == 200, resp.text
    result = resp.json()["result"]
    assert result.get("isError") in (None, False)
    payload = json.loads(result["content"][0]["text"])
    assert payload["cash"] == 100_000
    assert result["structuredContent"]["positions"] == []


def test_a_quote_comes_back_as_text_and_structured_content(client: TestClient, account) -> None:
    _, token = account
    resp = rpc(client, token, "tools/call", {"name": "get_quote", "arguments": {"ticker": "aapl"}})
    result = resp.json()["result"]
    assert result["structuredContent"]["ticker"] == "AAPL"
    assert result["structuredContent"]["price"] > 0


def test_a_tool_error_is_a_result_not_a_protocol_failure(client: TestClient, account) -> None:
    _, token = account
    resp = rpc(
        client, token, "tools/call", {"name": "get_quote", "arguments": {"ticker": "not a ticker"}}
    )
    assert resp.status_code == 200
    result = resp.json()["result"]
    assert result["isError"] is True
    assert "Unknown ticker" in result["content"][0]["text"]


def test_a_minted_connector_token_works_and_is_its_own_session(client: TestClient, account) -> None:
    uid, _ = account

    def scoped_db():
        session = SessionLocal()
        set_rls_user(session, uid)
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = scoped_db
    app.dependency_overrides[get_current_user] = lambda: User(id=uid, is_guest=True)
    try:
        minted = client.post("/api/v1/auth/mcp-token").json()
        assert minted["url_path"] == "/mcp"
        assert rpc(client, minted["token"], "tools/list").status_code == 200
        agents = [s["user_agent"] for s in client.get("/api/v1/auth/sessions").json()]
        assert "MCP connector" in agents
    finally:
        app.dependency_overrides.clear()
