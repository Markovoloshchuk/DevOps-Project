from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Analytics Service"
    assert "version" in data
    assert "app_env" in data
    assert "log_level" in data
    assert "core_service_status" in data


def test_stats_graceful_when_core_unreachable():
    # core_service недоступний у тестовому середовищі —
    # /stats має коректно повернути помилку, а не падати
    response = client.get("/stats")
    assert response.status_code == 200
    assert "error" in response.json()
