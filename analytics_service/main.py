import os

import httpx
from fastapi import FastAPI

app = FastAPI(title="Analytics Service")

# Отримуємо URL з змінних середовища Docker або використовуємо локальний за замовчуванням
CORE_SERVICE_URL = os.getenv("CORE_SERVICE_URL", "http://core_service:8000")


@app.get("/health")
def check_core_health():
    try:
        response = httpx.get(f"{CORE_SERVICE_URL}/")
        core_status = response.json().get("status", "unknown")
    except Exception as e:
        core_status = f"unreachable ({e!s})"

    return {
        "service": "Analytics Service",
        "core_service_status": core_status,
    }