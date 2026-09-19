import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_quick_log_hero():
    response = client.post("/api/v1/events/quick-log", json={
        "text": "Spool erection near V-105 completed today. 14 spools installed.",
        "project_id": "OIL-DNPE-2026",
        "submitted_by": "Site Supervisor"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["matched_activity_id"] == "PIP-L6-0427"
    assert data["confidence_tier"] in ["HIGH", "MEDIUM"]
    assert "Logged:" in data["confirmation_message"]

    assert data["extracted_fields"]["location"] == "V-105"

    # Also verify that the event appears in the review queue
    rq = client.get("/api/review-queue")
    assert rq.status_code == 200
    queue_items = rq.json()
    assert any(item["event_id"] == data["event_id"] for item in queue_items)

def test_quick_log_unmatched_requests_detail():
    response = client.post("/api/v1/events/quick-log", json={
        "text": "Catering van arrived at gate 3 with lunch packs.",
        "project_id": "OIL-DNPE-2026"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["needs_detail"] is True
    assert "clarification" in data["confirmation_message"].lower() or "detail" in data["confirmation_message"].lower()

def test_institutional_memory_history():
    response = client.get("/api/v1/insights/history")
    assert response.status_code == 200
    data = response.json()
    assert data["total_completed_activities"] >= 50
    assert len(data["discipline_summary"]) >= 5
    assert len(data["activities"]) >= 50
    
    # Check that discipline summary is sorted with most overrun days first
    summaries = data["discipline_summary"]
    for i in range(len(summaries) - 1):
        assert summaries[i]["overrun_days"] >= summaries[i+1]["overrun_days"]

def test_institutional_memory_filtered():
    response = client.get("/api/v1/insights/history?discipline=Civil")
    assert response.status_code == 200
    data = response.json()
    assert len(data["activities"]) >= 10
    assert all(a["discipline"] == "Civil" for a in data["activities"])
