from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "Core Service"}


def test_health_shows_config():
    # /health відображає конфігурацію з ConfigMap (APP_ENV тощо)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "app_env" in data
    assert "log_level" in data
    assert "default_event_level" in data


def test_create_and_read_event():
    # Тест створення нового запису журналу
    create_response = client.post(
        "/events/",
        params={"title": "Вимкнення сервера", "description": "Планове вимкнення"},
    )
    assert create_response.status_code == 200
    data = create_response.json()
    assert data["title"] == "Вимкнення сервера"
    assert data["level"] == "info"  # рівень за замовчуванням з конфігурації
    event_id = data["id"]

    # Тест зчитування створеного запису
    get_response = client.get(f"/events/{event_id}")
    assert get_response.status_code == 200
    assert get_response.json()["description"] == "Планове вимкнення"


def test_read_missing_event():
    response = client.get("/events/999999")
    assert response.status_code == 404