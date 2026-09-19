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

def test_get_matches_read_only_idempotent():
    # 1. Create a field event via quick-log
    log_res = client.post("/api/v1/events/quick-log", json={
        "text": "Hydrotesting completed on line 12 near TK-101 today.",
        "project_id": "OIL-DNPE-2026",
        "submitted_by": "Field Engineer"
    })
    assert log_res.status_code == 200
    evt_id = log_res.json()["event_id"]

    # 2. First GET /api/matches/{evt_id}
    res1 = client.get(f"/api/matches/{evt_id}")
    assert res1.status_code == 200
    data1 = res1.json()
    match_id1 = data1["match_id"]

    # 3. Second GET /api/matches/{evt_id} — should be read-only and return exact same match_id
    res2 = client.get(f"/api/matches/{evt_id}")
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["match_id"] == match_id1
    assert len(data2["top_candidates"]) == len(data1["top_candidates"])

def test_review_queue_filters_out_approved_items():
    # 1. Quick-log a hero activity
    log_res = client.post("/api/v1/events/quick-log", json={
        "text": "24-inch spool erected near V-105 today. 14 spools installed.",
        "project_id": "OIL-DNPE-2026",
        "submitted_by": "Site Supervisor"
    })
    assert log_res.status_code == 200
    evt_id = log_res.json()["event_id"]

    # 2. Confirm it appears in pending review queue
    q_pending = client.get("/api/review-queue?status=pending").json()
    match_item = next((item for item in q_pending if item["event_id"] == evt_id), None)
    assert match_item is not None
    match_id = match_item["match_id"]

    # 3. Approve it
    appr_res = client.post(f"/api/matches/{match_id}/approve", json={
        "decided_by": "Chief Planner",
        "notes": "Testing review queue filter"
    })
    assert appr_res.status_code == 200

    # 4. Confirm it is NO LONGER in pending review queue
    q_after = client.get("/api/review-queue?status=pending").json()
    assert not any(item["match_id"] == match_id for item in q_after)

    # 5. Confirm it DOES appear in resolved review queue
    q_resolved = client.get("/api/review-queue?status=resolved").json()
    assert any(item["match_id"] == match_id for item in q_resolved)

def test_institutional_memory_search_q():
    # Search by keyword e.g. "piping" or "erection"
    res = client.get("/api/v1/insights/history?q=piping")
    assert res.status_code == 200
    data = res.json()
    assert data["query"] == "piping"
    assert len(data["activities"]) > 0
    # Every returned record must match token in activity, description, discipline, or location
    for act in data["activities"]:
        full_text = f"{act['activity_id']} {act['description']} {act['discipline']} {act['location'] or ''} {act['source']}".lower()
        assert "piping" in full_text

def test_duplicate_approval_safeguard():
    # Attempting to re-approve an already approved match should be rejected safely
    # 1. Quick-log
    log_res = client.post("/api/v1/events/quick-log", json={
        "text": "24-inch spool erected near V-105 today.",
        "project_id": "OIL-DNPE-2026",
        "submitted_by": "Site Supervisor"
    })
    assert log_res.status_code == 200
    evt_id = log_res.json()["event_id"]

    matches_res = client.get(f"/api/matches/{evt_id}").json()
    match_id = matches_res["match_id"]

    # 2. Approve first time
    appr1 = client.post(f"/api/matches/{match_id}/approve", json={
        "decided_by": "Chief Planner"
    })
    assert appr1.status_code == 200

    # 3. Approve second time -> returns idempotent ALREADY_APPROVED status safely without re-mutating
    appr2 = client.post(f"/api/matches/{match_id}/approve", json={
        "decided_by": "Chief Planner"
    })
    assert appr2.status_code == 200
    assert appr2.json().get("status") == "ALREADY_APPROVED"

