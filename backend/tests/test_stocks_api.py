"""Endpoint tests using the fake provider (no network).

The search and quote endpoints don't touch Postgres, so these run hermetically
against the in-memory TestClient + local Redis. DB-backed history is verified
manually / via integration runs.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.market_data.fake_provider import FakeProvider
from app.services.market_data.registry import get_provider


@pytest.fixture
def fake_client() -> TestClient:
    app.dependency_overrides[get_provider] = lambda: FakeProvider()
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_search_endpoint(fake_client: TestClient) -> None:
    resp = fake_client.get("/api/v1/stocks/search", params={"q": "apple"})
    assert resp.status_code == 200
    symbols = [r["symbol"] for r in resp.json()]
    assert "AAPL" in symbols


def test_quote_endpoint(fake_client: TestClient) -> None:
    resp = fake_client.get("/api/v1/stocks/NVDA/quote")
    assert resp.status_code == 200
    body = resp.json()
    assert body["ticker"] == "NVDA"
    assert body["price"] > 0


def test_invalid_range_is_422(fake_client: TestClient) -> None:
    resp = fake_client.get("/api/v1/stocks/AAPL/history", params={"range": "99y"})
    assert resp.status_code == 422
