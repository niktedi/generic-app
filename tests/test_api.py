"""
Integration tests: spin up the app via TestClient and hit real routes.
Covers routing, serialization and the database layer end-to-end.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root():
    resp = client.get("/")
    assert resp.status_code == 200
    # Root serves the calendar single-page app.
    assert "text/html" in resp.headers["content-type"]


def test_healthz():
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_readyz_ok():
    # The database is reachable in tests -> ready.
    resp = client.get("/readyz")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ready"


def test_info():
    resp = client.get("/info")
    assert resp.status_code == 200
    assert resp.json()["app"] == "generic-app"


def test_login_creates_user():
    resp = client.post("/api/login", json={"name": "alice"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "alice"
    assert "id" in body


def test_login_idempotent():
    a = client.post("/api/login", json={"name": "bob"}).json()
    b = client.post("/api/login", json={"name": "bob"}).json()
    assert a["id"] == b["id"]  # same user, not a duplicate


def test_add_and_list_note():
    user = client.post("/api/login", json={"name": "carol"}).json()
    uid = user["id"]
    r = client.post(
        "/api/notes",
        json={"user_id": uid, "date": "2026-06-15", "content": "Dentist 10am"},
    )
    assert r.status_code == 200

    r = client.get("/api/notes", params={"user_id": uid, "year": 2026, "month": 6})
    assert r.status_code == 200
    notes = r.json()["notes"]
    assert len(notes) == 1
    assert notes[0]["content"] == "Dentist 10am"
    assert notes[0]["date"] == "2026-06-15"


def test_note_isolated_by_month():
    user = client.post("/api/login", json={"name": "dave"}).json()
    uid = user["id"]
    client.post(
        "/api/notes",
        json={"user_id": uid, "date": "2026-06-15", "content": "June"},
    )
    r = client.get("/api/notes", params={"user_id": uid, "year": 2026, "month": 7})
    assert r.json()["notes"] == []


def test_delete_note():
    user = client.post("/api/login", json={"name": "erin"}).json()
    uid = user["id"]
    note = client.post(
        "/api/notes",
        json={"user_id": uid, "date": "2026-06-15", "content": "temp"},
    ).json()
    r = client.delete(f"/api/notes/{note['id']}", params={"user_id": uid})
    assert r.status_code == 200


def test_delete_missing_note_404():
    user = client.post("/api/login", json={"name": "frank"}).json()
    r = client.delete("/api/notes/999999", params={"user_id": user["id"]})
    assert r.status_code == 404


def test_empty_content_rejected():
    user = client.post("/api/login", json={"name": "gina"}).json()
    r = client.post(
        "/api/notes",
        json={"user_id": user["id"], "date": "2026-06-15", "content": ""},
    )
    assert r.status_code == 422
