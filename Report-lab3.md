# Звіт з лабораторної роботи №3: Розгортання власного застосунку в Kubernetes

## Мета роботи
Описати мікросервісний застосунок «Журнал подій та інцидентів» (`core_service` +
`analytics_service` з лабораторних №1–2, PostgreSQL 16) набором маніфестів Kubernetes,
розгорнути його в локальному кластері minikube та продемонструвати керування життєвим
циклом засобами kubectl.

## Що було зроблено

**1. Образи застосунку.** Використано власні образи з попередніх лабораторних
(`core_service`, `analytics_service`, Dockerfile на FastAPI+uvicorn). Підготовлено дві
версії з конкретними тегами без `latest`: `1.0.0` і `1.1.0` (див. `screenshots/01-images.txt`).
Образи завантажені в minikube (`minikube image load`), CI публікує ті ж теги в GHCR при
створенні git-тега `v*`. Маніфести посилаються на `:1.0.0`.

**2. Локальний кластер.** Встановлено minikube, кластер запущено з драйвером docker
(`minikube start --driver=docker`). Вузол `minikube Ready`, системні поди в `kube-system`
`Running` (coredns, etcd, apiserver, scheduler, metrics-server тощо). Увімкнено доповнення
`metrics-server` та `ingress` (див. `screenshots/02-cluster.txt`).

**3. Namespace.** Створено окремий namespace `incident-journal` (`k8s/00-namespace.yaml`);
усі подальші об'єкти — лише в ньому.

**4. Маніфести (`k8s/`, по одному файлу на об'єкт, префікси 00–41 задають порядок):**
- Deployment `core-service` (2 репліки), `analytics-service` (2 репліки): узгоджені
  `labels/selector`, `requests/limits` CPU+memory, `liveness/readiness` `httpGet /health`;
- Service: `core-service` NodePort 30080, `analytics-service` NodePort 30081 (доступ з
  хоста через `minikube service --url` + всередині кластера), `postgres` ClusterIP;
- ConfigMap `app-config` (6 ключів: APP_ENV, LOG_LEVEL, DEFAULT_EVENT_LEVEL, CORE_TIMEOUT,
  DB_HOST, DB_PORT) — як `envFrom`; Secret `db-credentials` (DB_USER, DB_PASSWORD, DB_NAME,
  POSTGRES_PASSWORD — навчальні значення) — через `secretKeyRef`;
- Компонент зі станом: PostgreSQL 16 Deployment (стратегія Recreate, проби `pg_isready`)
  + PVC `postgres-pvc` 1Gi RWO + ClusterIP Service. Ingress-об'єкт не створювався —
  обрано варіант NodePort за завданням (аддон ingress при цьому увімкнено).

**5. Розгортання.** Усі маніфести застосовуються однією командою `kubectl apply -f k8s/`
(перевірено з нуля через `delete namespace` — див. `screenshots/05-deploy.txt`).
Перелік об'єктів: поди, Deployment, ReplicaSet, Service, PVC Bound. Застосунок відкрито
з хоста (`minikube service core-service --url`, `curl /health`, `/events/`, `/stats`).
Значення ConfigMap/Secret перевірені всередині контейнера (`kubectl exec ... env`) та
через відповідь `/health` (`app_env: production`) — див. `screenshots/06-config-events.txt`.
Створено 6 тестових подій, `/stats` повертає `{"total_events":6,"by_level":{"info":6}}`
(рівень `info` — дефолт із ConfigMap).

**6. Керування життєвим циклом** (див. `screenshots/06-lifecycle.txt`):
- a) видалення пода → ReplicaSet створив новий, сервіс не переривався;
- b) масштабування `core-service` до 3 реплік → endpoints показують 3 IP;
- c) оновлення образу `1.0.0 → 1.1.0` (`kubectl set image`) → `successfully rolled out`;
- d) історія (`rollout history`, ревізії 2, 3) та відкат (`rollout undo`) на `1.0.0`;
- e) доступність: 5 послідовних `GET /health` під час оновлення — усі `status: ok`.

**7. Діагностика** (див. `screenshots/07-diagnostics.txt`):
- навмисно вказано неіснуючий тег `bad-tag` → под `ImagePullBackOff`;
- причина знайдена через `describe pod` (`ErrImagePull`) та Events (`Failed to pull image ...
  bad-tag: not found`, `Back-off pulling image`);
- показано логи робочих реплік (`kubectl logs`, health-проби 200) та вхід у контейнер
  (`kubectl exec -- env`, APP_ENV/DB_HOST/DB_USER);
- помилку виправлено відкатом (`rollout undo`), фінальний стан — усі поди `Running`.

## Результат
Застосунок розгортається з нуля однією командою з каталогу `k8s/`, працює в окремому
namespace, конфігурація/секрети потрапляють у контейнери, життєвий цикл (self-heal, scale,
rolling update, rollback) та діагностика несправності продемонстровані зі збереженим
виводом команд у `screenshots/`. Усі 8 пунктів лабораторної роботи виконано.

Файли доказів: `screenshots/01-images.txt`, `02-cluster.txt`, `05-deploy.txt`,
`06-config-events.txt`, `06-lifecycle.txt`, `07-diagnostics.txt`.
