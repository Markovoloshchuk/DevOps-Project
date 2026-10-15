FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Версія образу (для демонстрації оновлення 1.0.0 -> 1.1.0).
ARG APP_VERSION=1.0.0
ENV APP_VERSION=${APP_VERSION}

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--ws", "none"]