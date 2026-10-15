import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture(scope="module")
def client():
    # Контекстний менеджер запускає lifespan -> init_db() з ретраями,
    # тому таблиці гарантовано створені перед тестами.
    # Без `with` TestClient lifespan не викликає — у цьому й була причина
    # падіння в CI: таблиця "events" не існувала.
    with TestClient(app) as c:
        yield c


def test_read_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "Core Service"}


def test_health_shows_config(client):
    # /health відображає конфігурацію з ConfigMap (APP_ENV тощо)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "app_env" in data
    assert "log_level" in data
    assert "default_event_level" in data


def test_create_and_read_event(client):
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


def test_read_missing_event(client):
    response = client.get("/events/999999")
    assert response.status_code == 404