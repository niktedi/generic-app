"""
Unit tests: exercise pure logic directly, no HTTP layer involved.
These are fast and isolated -- the base of the testing pyramid.
"""

import time

from app import health
from app.config import settings


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
    # Settings fall back to 'local' for pod/node when nothing is configured.
    monkeypatch.setattr(settings, "pod_name", "local")
    monkeypatch.setattr(settings, "node_name", "local")
    payload = health.info_payload()
    assert payload["pod"] == "local"
    assert payload["node"] == "local"
    assert payload["app"] == "generic-app"


def test_info_payload_reads_settings(monkeypatch):
    monkeypatch.setattr(settings, "pod_name", "generic-app-abc123")
    monkeypatch.setattr(settings, "node_name", "work1")
    payload = health.info_payload()
    assert payload["pod"] == "generic-app-abc123"
    assert payload["node"] == "work1"
