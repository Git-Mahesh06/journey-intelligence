
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "Journey Intelligence API is running"


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200


def test_dashboard_summary():
    response = client.get("/api/dashboard/summary")
    assert response.status_code == 200


def test_funnel_analytics():
    response = client.get("/api/analytics/funnel")
    assert response.status_code == 200


def test_anomaly_listing():
    response = client.get("/api/anomalies")
    assert response.status_code == 200


def test_session_timeline():
    response = client.get("/api/sessions/SES-2026-000602/events")
    assert response.status_code == 200
