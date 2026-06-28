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
