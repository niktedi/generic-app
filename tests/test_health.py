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
