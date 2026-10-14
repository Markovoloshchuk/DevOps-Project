import logging
import os

import httpx
from fastapi import FastAPI

# Конфігурація застосунку: підключається з ConfigMap у Kubernetes
# (у локальному розробленні — змінні оточення docker-compose).
APP_ENV = os.getenv("APP_ENV", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
CORE_SERVICE_URL = os.getenv("CORE_SERVICE_URL", "http://core_service:8000")
CORE_TIMEOUT = float(os.getenv("CORE_TIMEOUT", "3.0"))

logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger("analytics_service")

app = FastAPI(title="Analytics Service — Аналітика журналу подій")


@app.get("/health")
def check_core_health():
    """Статус core_service з обмеженим таймаутом (для проб і моніторингу)."""
    try:
        response = httpx.get(f"{CORE_SERVICE_URL}/health", timeout=CORE_TIMEOUT)
        core_status = response.json().get("status", "unknown")
    except Exception as e:
        core_status = f"unreachable ({e!s})"

    return {
        "service": "Analytics Service",
        "app_env": APP_ENV,
        "log_level": LOG_LEVEL,
        "core_service_status": core_status,
    }


@app.get("/stats")
def events_stats():
    """Аналітика журналу: кількість записів за рівнями важливості."""
    try:
        response = httpx.get(f"{CORE_SERVICE_URL}/events/", timeout=CORE_TIMEOUT)
        events = response.json()
    except Exception as e:
        logger.warning("core_service недоступний: %s", e)
        return {"error": f"core_service unreachable ({e!s})"}

    by_level: dict[str, int] = {}
    for event in events:
        level = event.get("level", "unknown")
        by_level[level] = by_level.get(level, 0) + 1

    return {"total_events": len(events), "by_level": by_level}