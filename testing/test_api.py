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


def test_unified_context_api_returns_documents_and_graph() -> None:
    response = client.post(
        "/analysis/context?asset_id=P101",
        json={"query": "Analyze P-101 vibration and identify related assets."},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["sources"]
    assert body["asset_relationships"]


def test_report_api_returns_pdf() -> None:
    response = client.post(
        "/reports/diagnostic",
        json={
            "asset_id": "P-101",
            "issue": "Abnormal vibration",
            "sources": [{"document": "01_P101_Inspection_Report.pdf", "page": 1}],
        },
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"


def test_analysis_run_returns_agent_trace_and_safety_decision() -> None:
    response = client.post(
        "/analysis/run?asset_id=P101",
        json={"query": "Analyze P-101 vibration and identify related assets."},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["agent_trace"]
    assert body["approval_status"] == "HUMAN_APPROVAL_REQUIRED"
    assert body["interrupt"]["type"] == "human_approval"


def test_demo_login_upload_and_approval_flow() -> None:
    login = client.post(
        "/auth/demo-login",
        data={"username": "engineer01", "password": "demo", "role": "Engineer"},
    )
    assert login.status_code == 200
    assert login.json()["role"] == "Engineer"

    upload = client.post(
        "/documents/upload",
        files={"file": ("demo.pdf", b"synthetic pdf bytes", "application/pdf")},
        data={"source": "Mechanical Maintenance", "version": "1.0"},
    )
    assert upload.status_code == 200
    assert upload.json()["trust_status"] == "trusted"
    assert len(upload.json()["sha256"]) == 64

    analysis = client.post(
        "/analysis/run?asset_id=P101",
        json={"query": "Analyze P-101 vibration and identify related assets."},
    )
    approval_id = analysis.json()["approval_id"]
    status = client.get(f"/approvals/{approval_id}")
    assert status.json()["status"] == "PENDING"
    decision = client.post(f"/approvals/{approval_id}/approve?username=engineer01")
    assert decision.json()["status"] == "APPROVED"


def test_frontend_and_report_download_routes() -> None:
    frontend = client.get("/app/")
    assert frontend.status_code == 200
    assert "APEX-AI" in frontend.text
