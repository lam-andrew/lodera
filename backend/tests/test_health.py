"""Tests for the health endpoint — the Sprint 1 skeleton's end-to-end contract check.

The database connectivity check is stubbed so these tests exercise the API contract without
requiring a running PostgreSQL instance (that path is covered by integration/CI runs).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def test_health_ok_when_db_connected(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.api.routes.check_database", lambda: True)

    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "connected"
    assert body["service"]
    assert body["version"]


def test_health_reports_db_unavailable_without_failing(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Backend stays up (200) even when the database is unreachable.
    monkeypatch.setattr("app.api.routes.check_database", lambda: False)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["database"] == "unavailable"


def test_health_reports_market_data_configuration(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The key is optional: /health reports whether market data (US-4) is configured."""
    monkeypatch.setattr("app.api.routes.check_database", lambda: True)

    monkeypatch.setattr("app.api.routes.settings.market_data_api_key", "")
    assert client.get("/health").json()["market_data"] == "unconfigured"

    monkeypatch.setattr("app.api.routes.settings.market_data_api_key", "a-test-token")
    assert client.get("/health").json()["market_data"] == "configured"
