import logging
import os
import time

from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import declarative_base, sessionmaker

logger = logging.getLogger(__name__)

# Підключення до PostgreSQL з конфігурацією через змінні оточення.
# Значення за замовчуванням відповідають локальному розробленню
# (docker-compose / k8s передають ці змінні з ConfigMap і Secret).
DB_USER = os.getenv("DB_USER", "app")
DB_PASSWORD = os.getenv("DB_PASSWORD", "app")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "events_db")
DB_CONNECT_RETRIES = int(os.getenv("DB_CONNECT_RETRIES", "10"))
DB_CONNECT_DELAY = float(os.getenv("DB_CONNECT_DELAY", "3.0"))

DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Event(Base):
    """Запис журналу подій / інцидентів."""

    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    level = Column(String, index=True, default="info")


def init_db() -> None:
    """Створює таблиці з повторними спробами.

    У Kubernetes под може стартувати раніше за PostgreSQL — чекаємо
    на доступність БД, доки не вичерпано ліміт спроб.
    """
    for attempt in range(1, DB_CONNECT_RETRIES + 1):
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("Підключення до БД встановлено (спроба %s)", attempt)
            return
        except SQLAlchemyError as e:
            logger.warning(
                "БД ще недоступна (спроба %s/%s): %s", attempt, DB_CONNECT_RETRIES, e
            )
            time.sleep(DB_CONNECT_DELAY)
    raise RuntimeError(f"Не вдалося підключитися до БД за {DB_CONNECT_RETRIES} спроб")