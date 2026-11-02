from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint_reports_database_up():
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert payload["checks"]["database"]["status"] == "up"
    assert payload["checks"]["redis"]["status"] == "unknown"
    assert payload["observability"]["log_format"] in {"plain", "json"}


def test_readiness_endpoint_is_healthy_in_test_env():
    with TestClient(app) as client:
        response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_liveness_endpoint_is_alive():
    with TestClient(app) as client:
        response = client.get("/live")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"
