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
