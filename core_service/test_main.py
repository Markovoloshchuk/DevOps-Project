from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "WONG!", "service": "Core Service"}


def test_create_and_read_item():
    # Тест створення нового запису
    create_response = client.post(
        "/items/", params={"title": "Тестовий елемент", "description": "Опис"}
    )
    assert create_response.status_code == 200
    data = create_response.json()
    assert data["title"] == "Тестовий елемент"
    item_id = data["id"]

    # Тест зчитування створеного запису
    get_response = client.get(f"/items/{item_id}")
    assert get_response.status_code == 200
    assert get_response.json()["description"] == "Опис"