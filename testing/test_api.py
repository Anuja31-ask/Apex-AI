from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_query_returns_evidence() -> None:
    response = client.post("/query", json={"query": "What vibration was observed in P-101?"})
    assert response.status_code == 200
    body = response.json()
    assert body["context"]
    assert body["sources"][0]["document"]
    assert body["sources"][0]["page"] >= 1


def test_mock_asset_api_is_read_only_contract() -> None:
    response = client.get("/internal/assets/P101")
    assert response.status_code == 200
    assert response.json()["asset_id"] == "P-101"
    assert response.json()["access"].startswith("read-only")


def test_graph_api_returns_asset_relationships() -> None:
    response = client.get("/graph/assets/P101")
    assert response.status_code == 200
    assert response.json()["backend"] == "memory"
    assert response.json()["relationship_count"] == 3
