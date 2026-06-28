"""
FastAPI application entrypoint.

Serves a small calendar web app plus Kubernetes-style health endpoints.

Web app:
  GET  /                 -> calendar single-page app (dark theme)
  POST /api/login        -> get-or-create a user by name
  GET  /api/notes        -> notes for a user in a given month
  POST /api/notes        -> add a note block to a day

Operational endpoints:
  GET /healthz   -> liveness probe target (is the process alive?)
  GET /readyz    -> readiness probe target (can it serve traffic?)
  GET /info      -> pod/node identity, handy to see HA load-balancing

The /healthz and /readyz split mirrors Kubernetes probe semantics:
  - livenessProbe  hits /healthz  -> if it fails, kubelet restarts the pod
  - readinessProbe hits /readyz   -> if it fails, pod is pulled from Service endpoints
"""

from pathlib import Path

from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app import db, health

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="generic-app", version="0.1.0")


# --- request models -------------------------------------------------------


class LoginRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class NoteRequest(BaseModel):
    user_id: int
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    content: str = Field(min_length=1, max_length=2000)


# --- web app --------------------------------------------------------------


@app.get("/")
def root() -> FileResponse:
    """Serve the calendar single-page app."""
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/login")
def login(req: LoginRequest) -> dict:
    """Return the user, creating it on first sight. No real auth — name only."""
    return db.get_or_create_user(req.name)


@app.get("/api/notes")
def list_notes(user_id: int, year: int, month: int) -> dict:
    """Return all of a user's notes for the requested calendar month."""
    return {"notes": db.get_notes_for_month(user_id, year, month)}


@app.post("/api/notes")
def create_note(req: NoteRequest) -> dict:
    """Append a single text block to a given day for a user."""
    if not req.content.strip():
        raise HTTPException(status_code=422, detail="content must not be empty")
    return db.add_note(req.user_id, req.date, req.content)


@app.delete("/api/notes/{note_id}")
def delete_note(note_id: int, user_id: int) -> dict:
    """Delete one of the user's own notes. 404 if it doesn't exist or isn't theirs."""
    if not db.delete_note(note_id, user_id):
        raise HTTPException(status_code=404, detail="note not found")
    return {"deleted": note_id}


# --- operational endpoints ------------------------------------------------


@app.get("/healthz")
def healthz() -> dict:
    """Liveness: process is up and responding."""
    return health.health_payload()


@app.get("/readyz")
def readyz(response: Response) -> dict:
    """
    Readiness: ready only if the database is reachable.

    Returns 503 when the DB is down so Kubernetes pulls the pod from the
    Service endpoints (but does NOT restart it — that's liveness's job).
    """
    if db.db_ready():
        return {"status": "ready"}
    response.status_code = 503
    return {"status": "not ready", "reason": "database unreachable"}


@app.get("/info")
def info() -> dict:
    return health.info_payload()


# Static assets (CSS/JS). Mounted last so it does not shadow API routes.
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
