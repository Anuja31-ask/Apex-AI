from fastapi.testclient import TestClient
from types import SimpleNamespace
from uuid import uuid4

from app.main import app
from app.core.database import get_db
from app.core.security import get_current_user
from backend.main import app as apex_app


client = TestClient(app)


class FakeDB:
    def add(self, _item):
        return None

    def flush(self):
        return None

    def commit(self):
        return None


fake_user = lambda: SimpleNamespace(id=uuid4(), username="test-engineer", role="ENGINEER", is_active=True)
apex_app.dependency_overrides[get_current_user] = fake_user
apex_app.dependency_overrides[get_db] = lambda: FakeDB()


def test_refineshield_root_remains_available() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "RefineShield backend is running"


def test_apex_health_is_mounted_under_refineshield() -> None:
    response = client.get("/apex/health")
    assert response.status_code == 200
    assert response.json()["service"] == "member4-rag"


def test_apex_analysis_is_available_under_refineshield() -> None:
    response = client.post(
        "/apex/analysis/run?asset_id=P101",
        json={"query": "Analyze P-101 vibration and identify related assets."},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["approval_status"] == "HUMAN_APPROVAL_REQUIRED"
    assert body["interrupt"]["type"] == "human_approval"
    assert body["thread_id"] == body["approval_id"]


def test_apex_frontend_is_available_under_refineshield() -> None:
    response = client.get("/apex/app/")
    assert response.status_code == 200
    assert "APEX-AI" in response.text
    assert "Create account" in response.text