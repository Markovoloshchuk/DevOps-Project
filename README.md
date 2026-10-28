# DevOps-Project — Журнал подій та інцидентів

Мікросервісний застосунок на FastAPI, що складається з двох сервісів:

- **`core_service`** — REST API для ведення журналу подій та інцидентів:
  - `POST /events/` — створення запису;
  - `GET /events/` — отримання списку записів;
  - `GET /events/{id}` — отримання запису за ID;
  - `GET /health` — перевірка стану сервісу.
  
  Дані зберігаються в **PostgreSQL**.

- **`analytics_service`** — сервіс аналітики журналу:
  - `GET /health` — перевірка стану та доступності `core_service`;
  - `GET /stats` — отримання кількості записів за рівнями важливості.

## Локальний запуск (Docker Compose)

```bash
docker compose up --build
```

Після запуску сервіси доступні за адресами:

- `core_service`: http://localhost:8000  
  OpenAPI-документація: http://localhost:8000/docs
- `analytics_service`: http://localhost:8001/health  
  Статистика: http://localhost:8001/stats
- PostgreSQL 16 — збереження даних у Docker volume `pg_data`.

## Розгортання в Kubernetes (Minikube)

Передумова: Docker-образи сервісів опубліковані в GitHub Container Registry (GHCR). У маніфестах Kubernetes потрібно використовувати відповідні доступні теги образів.

```bash
minikube start --driver=docker
minikube addons enable metrics-server
minikube addons enable ingress

# Застосувати всі маніфести з каталогу k8s/
kubectl apply -f k8s/

# Перевірити стан ресурсів
kubectl get all -n incident-journal
```

Доступ до застосунку:

- `core_service`: `http://<minikube-ip>:30080`  
  Альтернативний спосіб отримати адресу:
  ```bash
  minikube service core-service -n incident-journal --url
  ```
- `analytics_service`: `http://<minikube-ip>:30081`

Каталог `k8s/` містить маніфести Kubernetes. Числові префікси в назвах файлів допомагають застосовувати ресурси в логічному порядку: `Namespace` → `ConfigMap` / `Secret` → PostgreSQL із PVC → сервіси застосунку.

| Файл | Об'єкт |
|---|---|
| `00-namespace.yaml` | Namespace `incident-journal` |
| `10-configmap.yaml` | ConfigMap `app-config` |
| `11-secret.yaml` | Secret `db-credentials` |
| `20-postgres-pvc.yaml` | PersistentVolumeClaim `postgres-pvc` (1 Gi, RWO) |
| `21-postgres-deployment.yaml` | Deployment `postgres` (PostgreSQL 16, PVC) |
| `22-postgres-service.yaml` | Service `postgres` (ClusterIP) |
| `30-core-deployment.yaml` | Deployment `core-service` (2 репліки, probes, resources) |
| `31-core-service.yaml` | Service `core-service` (NodePort 30080) |
| `40-analytics-deployment.yaml` | Deployment `analytics-service` (2 репліки) |
| `41-analytics-service.yaml` | Service `analytics-service` (NodePort 30081) |

## Конфігурація: ConfigMap та Secret

### ConfigMap `app-config` — нечутливі параметри

| Параметр | Значення | Призначення |
|---|---|---|
| `APP_ENV` | `production` | Режим роботи застосунку; відображається в `/health` |
| `LOG_LEVEL` | `INFO` | Рівень логування в обох сервісах |
| `DEFAULT_EVENT_LEVEL` | `info` | Рівень важливості за замовчуванням для нових записів |
| `CORE_TIMEOUT` | `3.0` | Таймаут у секундах для викликів `analytics_service` → `core_service` |
| `DB_HOST` | `postgres` | Хост PostgreSQL — DNS-ім'я Kubernetes Service |
| `DB_PORT` | `5432` | Порт PostgreSQL |

### Secret `db-credentials` — чутливі параметри

| Параметр | Призначення |
|---|---|
| `DB_USER` | Користувач бази даних |
| `DB_PASSWORD` | Пароль бази даних; навчальне значення, не використовувати в production |
| `DB_NAME` | Назва бази даних |
| `POSTGRES_PASSWORD` | Пароль для ініціалізації контейнера PostgreSQL |

Значення передаються в контейнери як змінні оточення за допомогою `envFrom` та/або `secretKeyRef` у маніфестах Deployment.

Перевірити змінні оточення всередині Pod можна командою:

```bash
kubectl exec -n incident-journal <pod> -- env | grep -E 'APP_ENV|DB_'
```

Не виводьте паролі й інші секрети в публічні логи або звіти.

## CI/CD — GitHub Actions

CI/CD реалізовано за допомогою GitHub Actions у файлі `.github/workflows/ci.yml`.

Pipeline автоматично запускається під час `push` у `main` і створення Pull Request до `main`. Він охоплює такі етапи:

1. **Lint** — статичний аналіз коду за допомогою Ruff.
2. **Тестування** — запуск тестів сервісів; для тестів `core_service` використовується PostgreSQL.
3. **Збірка Docker-образів** — побудова образів сервісів після успішних перевірок.
4. **Сканування безпеки** — перевірка образів за допомогою Trivy, якщо цей етап увімкнено в конфігурації workflow.
5. **Публікація в GHCR** — після `push` у гілку `main` образи публікуються в GitHub Container Registry.

Перевірки виконуються в GitHub Actions, а їхній статус відображається у відповідному Pull Request. Невдалі обов'язкові перевірки мають блокувати злиття PR відповідно до налаштувань захисту гілки `main`.

Для опублікованих Docker-образів використовуються такі теги:

- **`sha`** — тег, пов'язаний із конкретним комітом;
- **`latest`** — тег останнього опублікованого образу з гілки `main`.

Публікація образів виконується лише для `push` у `main`, а не для Pull Request. Облікові дані для публікації налаштовуються в GitHub Actions permissions/secrets відповідно до конфігурації репозиторію.

Образи сервісів:

- `ghcr.io/markovoloshchuk/core_service`
- `ghcr.io/markovoloshchuk/analytics_service`

Приклад завантаження образу:

```bash
docker pull ghcr.io/markovoloshchuk/core_service:latest
docker pull ghcr.io/markovoloshchuk/analytics_service:latest
```

Для відтворюваного розгортання бажано використовувати тег `sha`, що відповідає потрібному коміту, замість змінного тегу `latest`.

## Тести

Для запуску тестів локально:

```bash
# core_service потребує доступного PostgreSQL
cd core_service
pytest -v
```

```bash
# analytics_service
cd analytics_service
pytest -v
```

Для локального тестування `core_service` запустіть необхідну інфраструктуру, наприклад через Docker Compose, і перевірте, що параметри підключення до PostgreSQL налаштовані відповідно до конфігурації проєкту.