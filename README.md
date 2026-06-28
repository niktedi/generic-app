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

```bash
uv sync                 # install deps from uv.lock into .venv
uv run ruff check .     # lint
uv run pytest           # test
uv run uvicorn app.main:app --reload --port 8000
# open http://127.0.0.1:8000/docs
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
