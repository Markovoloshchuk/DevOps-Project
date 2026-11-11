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

---

## Локальний запуск (Docker Compose)

```bash
docker compose up --build

```

Після запуску сервіси доступні за адресами:

* `core_service`: http://localhost:8000
OpenAPI-документація: http://localhost:8000/docs
* `analytics_service`: http://localhost:8001/health
Статистика: http://localhost:8001/stats
* PostgreSQL 16 — збереження даних у Docker volume `pg_data`.

---

## Розгортання в Kubernetes за допомогою Helm (Лабораторна робота №4)

Застосунок пакується у власний Helm-чарт, розташований у каталозі `chart/`. Це дозволяє параметризувати розгортання для різних середовищ та керувати повним життєвим циклом релізу.

### Структура Helm-чарта (`chart/`)

* `Chart.yaml` — метадані чарта.
* `values.yaml` — значення за замовчуванням (розробницьке середовище).
* `values-dev.yaml` / `values-prod.yaml` — файли значень для середовищ `dev` і `prod`.


* `templates/` — шаблони Kubernetes-маніфестів (Deployment, Service, PVC, ConfigMap, Secret тощо).
* `templates/_helpers.tpl` — іменовані шаблони для генерації імен та спільних міток.



### Різниця між `version` та `appVersion` у `Chart.yaml`

* **`version`** — версія самого Helm-чарта (наприклад, `0.1.0`). Вона змінюється під час оновлення логіки шаблонів, параметрів або структури розгортання в Kubernetes.
* **`appVersion`** — версія самого застосунку (наприклад, `1.0.0`), яка відповідає тегу розгорнутих Docker-образів мікросервісів.

---

### Параметри конфігурації `values.yaml`

Усі основні параметри винесені у файли значень. Нижче наведено опис основних параметрів конфігурації:

| Параметр | Тип | За замовчуванням (Dev) | Опис |
| --- | --- | --- | --- |
| `namespace` | string | `incident-journal` | Простір імен Kubernetes для розгортання |
| `environment` | string | `development` | Режим середовища (`development` / `production`) |
| `coreService.replicaCount` | int | `1` (у Prod — `2`) | Кількість реплік `core_service`

 |
| `coreService.image.repository` | string | `ghcr.io/markovoloshchuk/core_service` | Репозиторій образу `core_service` |
| `coreService.image.tag` | string | `1.0.0` | Тег образу `core_service`

 |
| `coreService.service.type` | string | `NodePort` | Тип Kubernetes Service для доступу

 |
| `coreService.service.nodePort` | int | `30080` | Зовнішній порт NodePort |
| `analyticsService.replicaCount` | int | `1` (у Prod — `2`) | Кількість реплік `analytics_service`

 |
| `analyticsService.image.repository` | string | `ghcr.io/markovoloshchuk/analytics_service` | Репозиторій образу `analytics_service` |
| `analyticsService.image.tag` | string | `1.0.0` | Тег образу `analytics_service`

 |
| `analyticsService.service.type` | string | `NodePort` | Тип Kubernetes Service

 |
| `analyticsService.service.nodePort` | int | `30081` | Зовнішній порт NodePort |
| `postgresql.replicaCount` | int | `1` | Кількість реплік бази даних |
| `postgresql.persistence.enabled` | bool | `true` | Увімкнення PersistentVolumeClaim для бази даних |
| `postgresql.persistence.size` | string | `1Gi` | Обсяг сховища для PostgreSQL |
| `ingress.enabled` | bool | `false` (у Prod — `true`) | Прапорець увімкнення Ingress-контролера

 |

---

### Команди встановлення та управління релізом

#### 1. Встановлення для середовища Розробки (Dev)

```bash
helm install my-app chart -f chart/values-dev.yaml -n incident-journal --create-namespace

```

#### 2. Встановлення для Продакшн середовища (Prod)

```bash
helm install my-app chart -f chart/values-prod.yaml -n incident-journal --create-namespace

```

#### 3. Життєвий цикл релізу

* Оновлення тегу образу "на льоту" через `--set`:


```bash
helm upgrade my-app chart -f chart/values-dev.yaml --set coreService.image.tag="1.0.1" -n incident-journal

```


* Оновлення середовища на Production:


```bash
helm upgrade my-app chart -f chart/values-prod.yaml -n incident-journal

```


* Перегляд історії ревізій:


```bash
helm history my-app -n incident-journal

```


* Відкат (Rollback) до попередньої стабільної ревізії:


```bash
helm rollback my-app <revision-number> -n incident-journal

```


* Видалення релізу:


```bash
helm uninstall my-app -n incident-journal

```



---

## Конфігурація: ConfigMap та Secret

### ConfigMap `app-config` — нечутливі параметри

| Параметр | Значення | Призначення |
| --- | --- | --- |
| `APP_ENV` | `production` / `development` | Режим роботи застосунку |
| `LOG_LEVEL` | `INFO` / `DEBUG` | Рівень логування в обох сервісах |
| `DEFAULT_EVENT_LEVEL` | `info` | Рівень важливості за замовчуванням |
| `CORE_TIMEOUT` | `3.0` | Таймаут у секундах для викликів `analytics_service` → `core_service` |
| `DB_HOST` | `postgres` | Хост PostgreSQL (DNS-ім'я Kubernetes Service) |
| `DB_PORT` | `5432` | Порт PostgreSQL |

### Secret `db-credentials` — чутливі параметри

| Параметр | Призначення |
| --- | --- |
| `DB_USER` | Користувач бази даних |
| `DB_PASSWORD` | Пароль бази даних (не зберігається у відкритому вигляді в шаблонах) |
| `DB_NAME` | Назва бази даних |
| `POSTGRES_PASSWORD` | Пароль для ініціалізації контейнера PostgreSQL |

Перевірити змінні оточення всередині Pod:

```bash
kubectl exec -n incident-journal <pod> -- env | grep -E 'APP_ENV|DB_'

```

---

## CI/CD — GitHub Actions

CI/CD реалізовано за допомогою GitHub Actions у файлі `.github/workflows/ci.yml`. Pipeline запускається при `push` у `main` та створенні PR:

1. **Lint** — статичний аналіз коду за допомогою Ruff.
2. **Тестування** — запуск тестів (`pytest`) із підключенням до PostgreSQL.
3. **Збірка Docker-образів** — побудова та перевірка контейнерів.
4. **Публікація в GHCR** — публікація образів у GitHub Container Registry при злитті в `main`.

Образи сервісів:

* `ghcr.io/markovoloshchuk/core_service`
* `ghcr.io/markovoloshchuk/analytics_service`

---

## Тести

Запуск тестів локально:

```bash
# core_service (потребує запущеного PostgreSQL)
cd core_service
pytest -v

```

```bash
# analytics_service
cd analytics_service
pytest -v

```
