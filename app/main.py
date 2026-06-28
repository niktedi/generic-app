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
