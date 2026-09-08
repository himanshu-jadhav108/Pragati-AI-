import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "PRAGATI AI" in data["service"]

def test_get_projects():
    response = client.get("/api/projects")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["id"] == "OIL-DNPE-2026"

def test_get_activities():
    response = client.get("/api/activities")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 10
    assert any(a["activity_id"] == "PIP-L6-0427" for a in data)

def test_dashboard_summary():
    response = client.get("/api/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert "planned_progress" in data
    assert "actual_progress" in data
    assert "schedule_variance" in data
    assert len(data["planned_vs_actual_curve"]) >= 5

def test_system_health():
    response = client.get("/api/health/system")
    assert response.status_code == 200
    data = response.json()
    assert data["backend"] == "healthy"
    assert data["database"] == "connected"
