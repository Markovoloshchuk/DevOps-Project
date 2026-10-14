# DevOps-Project — Журнал подій та інцидентів

Мікросервісний застосунок на FastAPI, що складається з двох сервісів:

- **`core_service`** — REST API для ведення журналу подій/інцидентів
  (`POST /events/`, `GET /events/`, `GET /events/{id}`), зберігання в **PostgreSQL**;
  легкий ендпоінт `GET /health` для проб і моніторингу.
- **`analytics_service`** — аналітика журналу: `GET /health` (статус core_service)
  та `GET /stats` (кількість записів за рівнями важливості).

## Локальний запуск (Docker Compose)

```bash
docker compose up --build
```

- core_service: <http://localhost:8000> (OpenAPI docs: `/docs`)
- analytics_service: <http://localhost:8001/health>, `/stats`
- PostgreSQL 16 з volume `pg_data`

## Розгортання в Kubernetes (minikube)

Передумова: образи опубліковані в GHCR з версійними тегами
(`ghcr.io/markovoloshchuk/core_service:1.0.0` та `:1.1.0` — створення git-тега
`v*` запускає CI, який публікує відповідний образ).

```bash
minikube start --driver=docker
minikube addons enable metrics-server
minikube addons enable ingress

# Розгортання всіх маніфестів однією командою з каталогу:
kubectl apply -f k8s/

# Стан об'єктів:
kubectl get all -n incident-journal

# Доступ до застосунку:
#   core_service     -> http://<minikube-ip>:30080  (або minikube service core-service -n incident-journal --url)
#   analytics_service -> http://<minikube-ip>:30081
```

Каталог `k8s/` містить по одному файлу на об'єкт; числові префікси гарантують
коректний порядок застосування (`namespace` → `ConfigMap`/`Secret` → `postgres`
з PVC → сервіси застосунку).

| Файл | Об'єкт |
|---|---|
| `00-namespace.yaml` | Namespace `incident-journal` |
| `10-configmap.yaml` | ConfigMap `app-config` |
| `11-secret.yaml` | Secret `db-credentials` |
| `20-postgres-pvc.yaml` | PersistentVolumeClaim `postgres-pvc` (1Gi, RWO) |
| `21-postgres-deployment.yaml` | Deployment `postgres` (PostgreSQL 16, PVC) |
| `22-postgres-service.yaml` | Service `postgres` (ClusterIP) |
| `30-core-deployment.yaml` | Deployment `core-service` (2 репліки, probes, resources) |
| `31-core-service.yaml` | Service `core-service` (NodePort 30080) |
| `40-analytics-deployment.yaml` | Deployment `analytics-service` (2 репліки) |
| `41-analytics-service.yaml` | Service `analytics-service` (NodePort 30081) |

## Конфігурація: ConfigMap та Secret

### ConfigMap `app-config` (нечутливі параметри)

| Параметр | Значення | Призначення |
|---|---|---|
| `APP_ENV` | `production` | Режим роботи застосунку (відображається в `/health`) |
| `LOG_LEVEL` | `INFO` | Рівень логування (logging в обох сервісах) |
| `DEFAULT_EVENT_LEVEL` | `info` | Рівень важливості за замовчуванням для нових записів журналу |
| `CORE_TIMEOUT` | `3.0` | Таймаут (с) викликів analytics → core_service |
| `DB_HOST` | `postgres` | Хост PostgreSQL (DNS-ім'я Service) |
| `DB_PORT` | `5432` | Порт PostgreSQL |

### Secret `db-credentials` (чутливі параметри)

| Параметр | Призначення |
|---|---|
| `DB_USER` | Користувач БД (використовується core_service та postgres) |
| `DB_PASSWORD` | Пароль БД (**навчальне значення**, не реальний пароль) |
| `DB_NAME` | Назва бази даних |
| `POSTGRES_PASSWORD` | Пароль ініціалізації контейнера PostgreSQL |

Усі значення підключаються до контейнерів як змінні оточення
(`envFrom`/`secretKeyRef` у Deployment). Перевірити потрапляння значень у
контейнер: `kubectl exec -n incident-journal <pod> -- env | grep -E 'APP_ENV|DB_'`.

## CI/CD

GitHub Actions (`.github/workflows/ci.yml`): lint (Ruff) → тести (з PostgreSQL
сервісом) → збірка образів + сканування Trivy → публікація в GHCR.

Публікація відбувається при `push` у `main` (теги `sha`, `latest`) та при
створенні git-тега `v*` (додається версійний тег, наприклад `v1.1.0` → `1.1.0`).

## Тести

```bash
# core_service потребує заповнений PostgreSQL (див. docker compose)
cd core_service && pytest -v

# analytics_service (без залежності від БД)
cd analytics_service && pytest -v
```
