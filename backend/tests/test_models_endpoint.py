from fastapi.testclient import TestClient


def test_models_endpoint_is_public_and_complete(client: TestClient) -> None:
    resp = client.get("/api/v1/models")
    assert resp.status_code == 200
    body = resp.json()
    # Transparency essentials are all present.
    assert body["data_sources"]
    assert len(body["features"]) > 0
    assert all("description" in f for f in body["features"])
    assert body["methodology"]
    assert body["limitations"]
    assert "not financial advice" in body["disclaimer"].lower()
