# generic-app

Dark-themed monthly calendar (FastAPI + PostgreSQL) used as the deploy target
for a self-hosted Kubernetes HA cluster GitOps pipeline.

Stack: Python 3.14 · FastAPI · uvicorn · uv · PostgreSQL (pg8000, raw SQL) ·
Alembic. Target: ghcr.io image -> ArgoCD -> k8s.

## Endpoints

| Method | Path                | Purpose                                        |
|--------|---------------------|------------------------------------------------|
| GET    | `/`                 | Calendar single-page app                       |
| POST   | `/api/login`        | Get-or-create a user by name (no auth)         |
| GET    | `/api/notes`        | List a user's notes for `?user_id&year&month`  |
| POST   | `/api/notes`        | Add a note block to a day                      |
| DELETE | `/api/notes/{id}`   | Delete one of the user's own notes             |
| GET    | `/healthz`          | Liveness probe (process alive)                 |
| GET    | `/readyz`           | Readiness probe (200 ok / 503 if DB is down)   |
| GET    | `/info`             | Pod/node identity (Downward API in k8s)        |

## Local development (uv)

Requires a running PostgreSQL (e.g. docker-compose) and a `.env` file
(copy `.env.example` and adjust). The schema is created by Alembic, not the
app, so apply migrations once before the first run.

```bash
uv sync                                  # install deps from uv.lock into .venv
uv run alembic upgrade head              # create/upgrade the DB schema
uv run ruff check .                      # lint
uv run pytest                            # test (needs a reachable Postgres)
uv run uvicorn app.main:app --reload --port 8000
# open http://127.0.0.1:8000
```

### Migrations (Alembic)

Migrations use raw SQL (`op.execute`) — no ORM models. The connection URL is
built from the same `DB_*` env vars the app uses (see `alembic/env.py`).

```bash
uv run alembic upgrade head      # apply all migrations
uv run alembic downgrade -1      # roll back one
uv run alembic current           # show the DB's current revision
uv run alembic history           # list migrations
```

## Docker (local)

```bash
uv export --no-dev --no-hashes -o requirements.txt   # refresh runtime deps for build
docker build -t generic-app:dev .
docker run --rm -p 8000:8000 generic-app:dev
curl http://127.0.0.1:8000/healthz
```

## Testing layers

- `tests/test_health.py` — unit tests against pure logic in `app/health.py` (fast, no HTTP).
- `tests/test_api.py` — integration tests via FastAPI `TestClient` (routes + validation).

## Next phases

- Phase 2 — GitHub Actions: lint -> test -> build -> push to ghcr.io.
- Phase 3 — self-hosted runner on work1/work2.
- Phase 4 — ArgoCD install + first Application; manifests in `kuber/`.
- Phase 5 — close the loop: CI bumps image tag in `kuber/`, ArgoCD deploys.
