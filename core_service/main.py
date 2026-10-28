import logging
import os
from contextlib import asynccontextmanager

from database import Event, SessionLocal, init_db
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

# Конфігурація застосунку: підключається з ConfigMap у Kubernetes
# (у локальному розробленні — змінні оточення docker-compose).
APP_ENV = os.getenv("APP_ENV", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
DEFAULT_EVENT_LEVEL = os.getenv("DEFAULT_EVENT_LEVEL", "info")
# Версія образу: тестувальники / CI можуть перевизначити через змінну оточення,
# демонстрація оновлення 1.0.0 -> 1.1.0 перевіряється через /health.
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")

logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger("core_service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ініціалізація БД при старті пода (з повторними спробами — див. database.py)
    init_db()
    yield


app = FastAPI(title="Core Service — Журнал подій", lifespan=lifespan)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def read_root():
    return {"status": "ok", "service": "Core Service"}


@app.get("/health")
def health():
    """Легкий ендпоінт для liveness/readiness проб; показує конфігурацію."""
    return {
        "status": "ok",
        "service": "Core Service",
        "version": APP_VERSION,
        "app_env": APP_ENV,
        "log_level": LOG_LEVEL,
        "default_event_level": DEFAULT_EVENT_LEVEL,
    }


@app.post("/events/")
def create_event(
    title: str,
    description: str,
    level: str | None = None,
    db: Session = Depends(get_db),
):
    event = Event(
        title=title,
        description=description,
        level=level or DEFAULT_EVENT_LEVEL,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    logger.info("Створено запис журналу: id=%s, level=%s", event.id, event.level)
    return event


@app.get("/events/")
def list_events(db: Session = Depends(get_db)):
    return db.query(Event).all()


@app.get("/events/{event_id}")
def read_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event