# generic-app — спецификация проекта (Фаза 1)

Документ-задание для Claude Code в VS Code. Проект инициализируется через **`uv`**, затем
наполняется по этой структуре. Цель Фазы 1 — готовое FastAPI-приложение с тестами и
Dockerfile, которое в следующих фазах ляжет под GitHub Actions (CI → ghcr.io) и ArgoCD (CD).

Стек: **Python 3.14 · FastAPI · uvicorn**. Менеджер пакетов и окружения — **`uv`**.

> Важно про именование: папка с Kubernetes-манифестами называется **`kuber/`** (не `k8s/`).
> Это наша осознанная договорённость для этого проекта.

---

## 0. Инициализация через uv (делает пользователь вручную ДО Claude Code)

```bash
# Создать проект (application layout, не библиотека)
uv init generic-app --python 3.14
cd generic-app

# Рантайм-зависимости
uv add fastapi "uvicorn[standard]"

# Dev/тест-зависимости в отдельную группу
uv add --dev pytest httpx ruff
```

После этого `uv` создаст `pyproject.toml`, `uv.lock`, `.venv/`, `.python-version` и заготовку
`main.py` / `hello.py`. **Эту заготовку удаляем** — структуру ниже создаёт Claude Code.

Запуск любой команды в окружении uv — через `uv run` (например `uv run pytest`,
`uv run uvicorn ...`). Отдельно активировать venv не обязательно.

---

## 1. Полная структура проекта

```
generic-app/
├── app/                          # пакет приложения
│   ├── __init__.py               # версия пакета
│   ├── main.py                   # FastAPI app + роуты
│   └── health.py                 # чистая бизнес-логика (тестируется без HTTP)
├── tests/
│   ├── __init__.py
│   ├── test_health.py            # unit-тесты (логика напрямую)
│   └── test_api.py               # integration-тесты (FastAPI TestClient)
├── kuber/                        # Kubernetes-манифесты (наполняется в Фазе 4)
│   └── .gitkeep
├── .github/
│   └── workflows/                # GitHub Actions CI (Фаза 2)
│       └── .gitkeep
├── Dockerfile                    # multi-stage, non-root, healthcheck
├── .dockerignore
├── .gitignore                    # (uv создаёт базовый; дополнить при необходимости)
├── pyproject.toml                # uv создаёт; дополнить конфигом pytest + ruff
├── uv.lock                       # lock-файл (создаёт uv, коммитить В репо)
├── .python-version               # создаёт uv
└── README.md
```

Папки `kuber/` и `.github/workflows/` пока пустые — кладём в каждую файл `.gitkeep`,
чтобы Git их зафиксировал.

---

## 2. Содержимое файлов

### `app/__init__.py`
```python
"""FastAPI demo application for k8s HA cluster GitOps pipeline."""

__version__ = "0.1.0"
```

### `app/health.py`
Чистая логика, намеренно отделённая от роутинга. Так её можно юнит-тестировать напрямую,
без HTTP-клиента. Роуты живут в `main.py` и покрыты интеграционными тестами.

```python
"""
Pure business logic, deliberately separated from FastAPI routing.

Why separate? So we can unit-test the logic directly (test_health.py)
without spinning up an HTTP client. Routing lives in main.py and is
covered by integration tests (test_api.py). This is the classic
'thin controller, testable core' split.
"""

import os
import time
from datetime import UTC, datetime

# Process start time, captured once at import.
_START_TIME = time.monotonic()


def uptime_seconds() -> float:
    """Seconds since the module was imported (process start)."""
    return round(time.monotonic() - _START_TIME, 3)


def health_payload() -> dict:
    """Build the /healthz response body."""
    return {
        "status": "ok",
        "uptime_seconds": uptime_seconds(),
        "timestamp": datetime.now(UTC).isoformat(),
    }


def info_payload() -> dict:
    """
    Build the /info response body.

    POD_NAME / NODE_NAME come from the Kubernetes Downward API
    (we'll wire these in the Deployment manifest in Phase 4).
    Falling back to 'local' makes the app run identically on your laptop.
    """
    return {
        "app": "generic-app",
        "version": os.getenv("APP_VERSION", "dev"),
        "pod": os.getenv("POD_NAME", "local"),
        "node": os.getenv("NODE_NAME", "local"),
    }


def add(a: int, b: int) -> int:
    """Trivial pure function to demonstrate a basic unit test."""
    return a + b
```

### `app/main.py`
Эндпоинты `/healthz` и `/readyz` намеренно разделены — это зеркало семантики проб
Kubernetes: liveness бьёт в `/healthz` (если упал — kubelet перезапускает под),
readiness бьёт в `/readyz` (если не готов — под убирают из endpoints Service).

```python
"""
FastAPI application entrypoint.

Endpoints:
  GET /          -> hello root
  GET /healthz   -> liveness probe target (is the process alive?)
  GET /readyz    -> readiness probe target (can it serve traffic?)
  GET /info      -> pod/node identity, handy to see HA load-balancing
  GET /add       -> demo endpoint exercising business logic

The /healthz and /readyz split mirrors Kubernetes probe semantics:
  - livenessProbe  hits /healthz  -> if it fails, kubelet restarts the pod
  - readinessProbe hits /readyz   -> if it fails, pod is pulled from Service endpoints
"""

from fastapi import FastAPI

from app import health
from app.health import add as add_logic

app = FastAPI(title="generic-app", version="0.1.0")


@app.get("/")
def root() -> dict:
    return {"message": "Hello from FastAPI on Kubernetes HA cluster"}


@app.get("/healthz")
def healthz() -> dict:
    """Liveness: process is up and responding."""
    return health.health_payload()


@app.get("/readyz")
def readyz() -> dict:
    """
    Readiness: app is ready to serve traffic.
    For now identical to liveness; later you'd check DB connections,
    cache warm-up, etc. here before returning ok.
    """
    return {"status": "ready"}


@app.get("/info")
def info() -> dict:
    return health.info_payload()


@app.get("/add")
def add(a: int, b: int) -> dict:
    return {"a": a, "b": b, "result": add_logic(a, b)}
```

### `tests/__init__.py`
Пустой файл (маркер пакета).

### `tests/test_health.py`
Юнит-тесты: прогоняют чистую логику напрямую, без HTTP. Быстрые и изолированные —
основание пирамиды тестирования.

```python
"""
Unit tests: exercise pure logic directly, no HTTP layer involved.
These are fast and isolated -- the base of the testing pyramid.
"""

import time

from app import health


def test_add():
    assert health.add(2, 3) == 5
    assert health.add(-1, 1) == 0


def test_health_payload_structure():
    payload = health.health_payload()
    assert payload["status"] == "ok"
    assert "uptime_seconds" in payload
    assert "timestamp" in payload


def test_uptime_increases():
    first = health.uptime_seconds()
    time.sleep(0.01)
    second = health.uptime_seconds()
    assert second >= first


def test_info_payload_defaults(monkeypatch):
    # Ensure env-driven fields fall back to 'local' when unset.
    monkeypatch.delenv("POD_NAME", raising=False)
    monkeypatch.delenv("NODE_NAME", raising=False)
    payload = health.info_payload()
    assert payload["pod"] == "local"
    assert payload["node"] == "local"
    assert payload["app"] == "generic-app"


def test_info_payload_reads_env(monkeypatch):
    monkeypatch.setenv("POD_NAME", "generic-app-abc123")
    monkeypatch.setenv("NODE_NAME", "work1")
    payload = health.info_payload()
    assert payload["pod"] == "generic-app-abc123"
    assert payload["node"] == "work1"
```

### `tests/test_api.py`
Интеграционные тесты: поднимают приложение через `TestClient` и бьют по реальным роутам.
Покрывают слой роутинга + сериализации, который юнит-тесты пропускают.

```python
"""
Integration tests: spin up the app via TestClient and hit real routes.
Covers the routing + serialization layer that unit tests skip.
This is the middle of the testing pyramid.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "message" in resp.json()


def test_healthz():
    resp = client.get("/healthz")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "uptime_seconds" in body


def test_readyz():
    resp = client.get("/readyz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ready"}


def test_info():
    resp = client.get("/info")
    assert resp.status_code == 200
    body = resp.json()
    assert body["app"] == "generic-app"
    assert "pod" in body
    assert "node" in body


def test_add_endpoint():
    resp = client.get("/add", params={"a": 7, "b": 5})
    assert resp.status_code == 200
    assert resp.json()["result"] == 12


def test_add_endpoint_validation():
    # FastAPI should reject non-int query params with 422.
    resp = client.get("/add", params={"a": "foo", "b": 5})
    assert resp.status_code == 422
```

---

## 3. Конфигурация `pyproject.toml`

`uv` уже создал секцию `[project]` с зависимостями. **Добавить** к ней блоки pytest и ruff.
Итоговый файл должен выглядеть примерно так (версии зависимостей уже проставит uv —
ниже показаны актуальные на июнь 2026 как ориентир):

```toml
[project]
name = "generic-app"
version = "0.1.0"
description = "FastAPI demo app for k8s HA cluster GitOps pipeline"
requires-python = ">=3.14"
dependencies = [
    "fastapi>=0.138.1",
    "uvicorn[standard]>=0.49.0",
]

[dependency-groups]
dev = [
    "pytest>=9.1.1",
    "httpx>=0.28.1",
    "ruff>=0.15.20",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = "-v --tb=short"

[tool.ruff]
line-length = 100
target-version = "py314"

[tool.ruff.lint]
# E/W: pycodestyle, F: pyflakes, I: isort, B: bugbear, UP: pyupgrade
select = ["E", "W", "F", "I", "B", "UP"]
```

> Примечание: `uv` пишет dev-зависимости в `[dependency-groups]` (стандарт PEP 735).
> Если в твоей версии uv формат иной — оставь как сгенерировал uv, важно лишь чтобы
> pytest/httpx/ruff были в dev-группе, а не в рантайме.

---

## 4. `Dockerfile`

Multi-stage сборка (build-инструменты не попадают в финальный образ), non-root пользователь,
container-level healthcheck. Запускающая команда — та же, что для локального uvicorn.

> Важно: внутри образа **uv не нужен**. Зависимости ставятся обычным `pip` из
> экспортированного списка. Образ должен быть минимальным и не тащить менеджер окружения.
> Поэтому в builder-стадии экспортируем зависимости из uv в `requirements.txt`:
> Claude Code должен сгенерировать `requirements.txt` командой
> `uv export --no-dev --no-hashes -o requirements.txt` и закоммитить его — он нужен только
> для Docker-сборки (рантайм-зависимости, без dev). Для локальной разработки источник
> правды — `pyproject.toml` + `uv.lock`.

```dockerfile
# ---- Stage 1: build dependencies ----
# Multi-stage keeps the final image small: build tools stay in the
# builder stage and never ship to production.
FROM python:3.14-slim AS builder

WORKDIR /build

# requirements.txt is exported from uv (runtime deps only):
#   uv export --no-dev --no-hashes -o requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ---- Stage 2: runtime ----
FROM python:3.14-slim

# Non-root user. Running as root in a container is a security anti-pattern;
# k8s securityContext will also enforce this in Phase 4.
RUN groupadd --gid 10001 appgroup \
    && useradd --uid 10001 --gid appgroup --no-create-home --shell /usr/sbin/nologin appuser

WORKDIR /app

COPY --from=builder /install /usr/local
COPY app/ ./app/

# APP_VERSION is overridden at build time (CI passes the git sha/tag).
ENV APP_VERSION=dev \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER appuser

EXPOSE 8000

# Container-level healthcheck (independent of k8s probes; useful with plain docker).
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/healthz').status==200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 5. `.dockerignore`

```
__pycache__/
*.pyc
*.pyo
.pytest_cache/
.ruff_cache/
.git/
.github/
.venv/
tests/
kuber/
*.md
.env
.gitignore
.dockerignore
Dockerfile
uv.lock
```

---

## 6. `.gitignore`

`uv init` создаёт базовый `.gitignore`. Убедиться, что в нём есть как минимум:

```
__pycache__/
*.py[cod]
.pytest_cache/
.ruff_cache/
.venv/
.env
*.egg-info/
.coverage
```

**Важно:** `uv.lock` и `.python-version` — **коммитим** (не в ignore). `requirements.txt`
(экспортированный для Docker) — тоже коммитим.

---

## 7. `kuber/.gitkeep` и `.github/workflows/.gitkeep`

Пустые файлы-заглушки, чтобы Git зафиксировал пустые папки до Фаз 2 и 4.

---

## 8. `README.md`

```markdown
# generic-app

Demo FastAPI service for the self-hosted Kubernetes HA cluster GitOps pipeline.

Stack: Python 3.14 · FastAPI · uvicorn · uv. Target: ghcr.io image -> ArgoCD -> k8s.

## Endpoints

| Method | Path       | Purpose                                  |
|--------|------------|------------------------------------------|
| GET    | `/`        | Hello root                               |
| GET    | `/healthz` | Liveness probe (process alive)           |
| GET    | `/readyz`  | Readiness probe (ready for traffic)      |
| GET    | `/info`    | Pod/node identity (Downward API in k8s)  |
| GET    | `/add`     | Demo: `?a=2&b=3` -> `{"result": 5}`      |

## Local development (uv)

​```bash
uv sync                 # install deps from uv.lock into .venv
uv run ruff check .     # lint
uv run pytest           # test
uv run uvicorn app.main:app --reload --port 8000
# open http://127.0.0.1:8000/docs
​```

## Docker (local)

​```bash
uv export --no-dev --no-hashes -o requirements.txt   # refresh runtime deps for build
docker build -t generic-app:dev .
docker run --rm -p 8000:8000 generic-app:dev
curl http://127.0.0.1:8000/healthz
​```

## Testing layers

- `tests/test_health.py` — unit tests against pure logic in `app/health.py` (fast, no HTTP).
- `tests/test_api.py` — integration tests via FastAPI `TestClient` (routes + validation).

## Next phases

- Phase 2 — GitHub Actions: lint -> test -> build -> push to ghcr.io.
- Phase 3 — self-hosted runner on work1/work2.
- Phase 4 — ArgoCD install + first Application; manifests in `kuber/`.
- Phase 5 — close the loop: CI bumps image tag in `kuber/`, ArgoCD deploys.
```

---

## 9. Финальная проверка (выполнить после сборки)

```bash
uv run ruff check .        # должно быть: All checks passed!
uv run pytest              # должно быть: 11 passed
uv run uvicorn app.main:app --port 8000   # затем curl http://127.0.0.1:8000/healthz
```

Когда `ruff` чистый и **11 тестов** проходят — Фаза 1 закрыта, переходим к Фазе 2
(GitHub Actions CI).

---

## Сводка задач для Claude Code

1. Удалить заготовку, созданную `uv init` (`main.py`/`hello.py` в корне).
2. Создать пакет `app/` с тремя файлами по разделу 2.
3. Создать `tests/` с тремя файлами по разделу 2.
4. Дополнить `pyproject.toml` блоками pytest и ruff (раздел 3).
5. Создать `Dockerfile` и `.dockerignore` (разделы 4–5).
6. Проверить/дополнить `.gitignore` (раздел 6).
7. Создать пустые `kuber/.gitkeep` и `.github/workflows/.gitkeep`.
8. Сгенерировать `requirements.txt` через `uv export --no-dev --no-hashes -o requirements.txt`.
9. Создать `README.md` (раздел 8).
10. Прогнать финальную проверку (раздел 9): ruff чистый, 11 тестов passed.
```
