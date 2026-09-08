import pytest
from datetime import datetime
from backend.app.db.session import SessionLocal
from backend.app.models.entities import Match, Activity, FieldEvent, AuditLog, Document
from backend.app.services.validation.approval_service import ApprovalService

@pytest.fixture
def db_session():
    db = SessionLocal()
    yield db
    db.close()

import uuid

@pytest.fixture
def sample_match(db_session):
    uid = str(uuid.uuid4())[:8]
    doc = db_session.query(Document).first()
    if not doc:
        doc = Document(id=f"DOC-TEST-{uid}", filename="test.txt", file_type="txt", project_id="OIL-DNPE-2026")
        db_session.add(doc)
        db_session.commit()

    activity = db_session.query(Activity).filter(Activity.activity_id == "PIP-L6-0427").first()
    assert activity is not None

    event = FieldEvent(
        id=f"EVT-TEST-GOV-{uid}",
        document_id=doc.id,
        raw_text="Spool erection completed at V-105. 14 spools installed.",
        evidence_text="Spool erection completed at V-105. 14 spools installed.",
        event_date="2026-03-08",
        discipline="Piping",
        location="V-105",
        equipment_id="V-105",
        status="COMPLETED",
        progress_percent=100.0,
        quantity=14.0,
        unit="spools"
    )
    db_session.add(event)
    db_session.flush()

    match = Match(
        id=f"MTH-TEST-GOV-{uid}",
        event_id=event.id,
        activity_id=activity.activity_id,
        score_semantic=0.85,
        score_discipline=1.0,
        score_entity=1.0,
        score_location=1.0,
        score_temporal=1.0,
        final_score=0.92,
        rank=1,
        confidence_tier="HIGH",
        decision="PENDING"
    )
    db_session.add(match)
    db_session.commit()

    return match

def test_approval_updates_schedule_and_creates_audit(db_session, sample_match):
    act_id = sample_match.activity_id
    activity = db_session.query(Activity).filter(Activity.activity_id == act_id).first()
    initial_prog = activity.actual_progress

    # Approve match
    result = ApprovalService.approve_match(db_session, match_id=sample_match.id, decided_by="Chief Planner Test")
    assert result["message"] == "Update approved and committed to schedule"
    
    # Verify activity was updated
    db_session.refresh(activity)
    assert activity.actual_progress >= initial_prog
    assert sample_match.decision == "APPROVED"

    # Verify audit log exists
    audit = db_session.query(AuditLog).filter(AuditLog.match_id == sample_match.id).first()
    assert audit is not None
    assert audit.action == "APPROVE"
    assert audit.final_activity_id == act_id

def test_idempotency_duplicate_approval(db_session, sample_match):
    # First approval
    ApprovalService.approve_match(db_session, match_id=sample_match.id, decided_by="Chief Planner Test")
    
    # Duplicate approval must not error and must report already approved
    result = ApprovalService.approve_match(db_session, match_id=sample_match.id, decided_by="Chief Planner Test")
    assert result["status"] == "ALREADY_APPROVED"

def test_reject_leaves_schedule_untouched(db_session):
    activity = db_session.query(Activity).filter(Activity.activity_id == "PIP-L6-0427").first()
    prev_prog = activity.actual_progress
    uid = str(uuid.uuid4())[:8]

    event = FieldEvent(
        id=f"EVT-TEST-REJECT-{uid}",
        document_id="DPR-TEST",
        raw_text="Random unrelated activity",
        discipline="Piping"
    )
    db_session.add(event)
    db_session.flush()

    match = Match(
        id=f"MTH-TEST-REJECT-{uid}",
        event_id=event.id,
        activity_id=activity.activity_id,
        final_score=0.45,
        decision="PENDING"
    )
    db_session.add(match)
    db_session.commit()

    result = ApprovalService.reject_match(db_session, match.id, decided_by="Chief Planner", reason="Test rejection")
    assert result["status"] == "REJECTED"
    assert match.decision == "REJECTED"

    db_session.refresh(activity)
    assert activity.actual_progress == prev_prog
