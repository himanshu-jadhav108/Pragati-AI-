import os
import shutil
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.app.db.session import get_db
from backend.app.models.entities import Project, Activity, Document, FieldEvent, Match, AuditLog
from backend.app.schemas.schemas import (
    ProjectResponse,
    ActivityResponse,
    DocumentResponse,
    FieldEventResponse,
    EventMatchesResponse,
    ApproveMatchRequest,
    EditMatchRequest,
    RejectMatchRequest,
    AuditLogResponse,
    DashboardSummaryResponse
)
from backend.app.services.ingestion.schedule_importer import (
    parse_csv_data,
    parse_xlsx_data,
    import_schedule_to_db
)
from backend.app.services.ingestion.document_parser import parse_uploaded_document
from backend.app.services.extraction.extractor import get_extractor
from backend.app.services.matching.matching_engine import MatchingEngine
from backend.app.services.validation.approval_service import ApprovalService
from backend.app.services.analytics.dashboard_service import DashboardService
from backend.app.core.config import settings

router = APIRouter()

# 1. Projects
@router.get("/projects", response_model=List[ProjectResponse])
def get_projects(db: Session = Depends(get_db)):
    return db.query(Project).all()

# 2. Activities
@router.get("/activities", response_model=List[ActivityResponse])
def get_activities(
    project_id: str = "OIL-DNPE-2026",
    discipline: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Activity).filter(Activity.project_id == project_id)
    if discipline:
        query = query.filter(Activity.discipline == discipline)
    if status:
        query = query.filter(Activity.status == status)
    return query.all()

# 3. Schedule Import (CSV or XLSX)
@router.post("/schedules/import")
async def import_schedule(
    file: UploadFile = File(...),
    project_id: str = Form("OIL-DNPE-2026"),
    db: Session = Depends(get_db)
):
    contents = await file.read()
    filename = file.filename.lower()
    
    try:
        if filename.endswith(".csv"):
            text = contents.decode("utf-8", errors="replace")
            rows = parse_csv_data(text)
        elif filename.endswith(".xlsx"):
            rows = parse_xlsx_data(contents)
        else:
            raise HTTPException(status_code=400, detail="Only .csv and .xlsx schedule formats are supported")
            
        imported_count, errors = import_schedule_to_db(db, project_id, rows)
        return {
            "status": "success",
            "imported_activities": imported_count,
            "filename": file.filename,
            "errors": errors
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to import schedule: {str(e)}")

# 4. Document Upload
@router.post("/documents", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    project_id: str = Form("OIL-DNPE-2026"),
    uploaded_by: str = Form("Site Engineer"),
    db: Session = Depends(get_db)
):
    contents = await file.read()
    file_type, extracted_text = parse_uploaded_document(file.filename, contents)
    
    doc = Document(
        project_id=project_id,
        filename=file.filename,
        file_type=file_type,
        file_size=len(contents),
        raw_text=extracted_text,
        uploaded_by=uploaded_by
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc

# 5. Extract Events from Document
@router.post("/extractions/{document_id}/run")
def run_extraction(document_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    extractor = get_extractor()
    provider_name = "live_gemini" if settings.AI_PROVIDER == "gemini" and settings.GEMINI_API_KEY else "deterministic_fallback"
    
    extracted_items = extractor.extract_events(doc.raw_text or "", metadata={"filename": doc.filename})
    
    saved_events = []
    engine = MatchingEngine(db, project_id=doc.project_id)
    
    for item in extracted_items:
        evt = FieldEvent(
            document_id=doc.id,
            raw_text=item.evidence_text or item.activity_description,
            event_date=item.event_date,
            discipline=item.discipline,
            activity_description=item.activity_description,
            location=item.location,
            equipment_id=item.equipment_id,
            status=item.status,
            progress_percent=item.progress_percent,
            quantity=item.quantity,
            unit=item.unit,
            evidence_text=item.evidence_text,
            extraction_provider=provider_name
        )
        db.add(evt)
        db.flush()
        
        # Run matching engine for this event
        engine.process_and_persist_matches(evt)
        saved_events.append(evt)
        
    db.commit()
    return {
        "status": "success",
        "document_id": doc.id,
        "extracted_events_count": len(saved_events),
        "provider": provider_name
    }

# 6. Events
@router.get("/events", response_model=List[FieldEventResponse])
def get_events(document_id: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(FieldEvent)
    if document_id:
        query = query.filter(FieldEvent.document_id == document_id)
    return query.order_by(FieldEvent.created_at.desc()).all()

# 7. Matches for a specific Event
@router.get("/matches/{event_id}", response_model=EventMatchesResponse)
def get_matches_for_event(event_id: str, db: Session = Depends(get_db)):
    event = db.query(FieldEvent).filter(FieldEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Field event not found")
        
    engine = MatchingEngine(db, project_id=event.document.project_id if event.document else "OIL-DNPE-2026")
    return engine.process_and_persist_matches(event)

# 8. Review Queue (All pending matches)
@router.get("/review-queue")
def get_review_queue(
    confidence: Optional[str] = None,
    discipline: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = (
        db.query(Match)
        .filter(Match.rank == 1)
        .order_by(Match.created_at.desc())
    )
    if confidence:
        query = query.filter(Match.confidence_tier == confidence)
        
    matches = query.all()
    results = []
    for m in matches:
        evt = m.event
        if discipline and evt.discipline != discipline:
            continue
        results.append({
            "match_id": m.id,
            "event_id": evt.id,
            "document_filename": evt.document.filename if evt.document else "Direct Entry",
            "raw_text": evt.raw_text,
            "evidence_text": evt.evidence_text,
            "activity_id": m.activity_id,
            "activity_description": m.candidate_activity.description if m.candidate_activity else "No matching activity",
            "discipline": evt.discipline or (m.candidate_activity.discipline if m.candidate_activity else "Unknown"),
            "location": evt.location or (m.candidate_activity.location if m.candidate_activity else "-"),
            "final_score": m.final_score,
            "confidence_tier": m.confidence_tier,
            "decision": m.decision,
            "scores": {
                "semantic": m.score_semantic,
                "discipline": m.score_discipline,
                "entity": m.score_entity,
                "location": m.score_location,
                "temporal": m.score_temporal,
                "penalty": m.penalty_contradiction
            },
            "created_at": m.created_at
        })
    return results

# 9. Governance: Approve Match
@router.post("/matches/{match_id}/approve")
def approve_match(match_id: str, req: ApproveMatchRequest, db: Session = Depends(get_db)):
    return ApprovalService.approve_match(db, match_id, decided_by=req.decided_by, notes=req.notes)

# 10. Governance: Edit Match
@router.post("/matches/{match_id}/edit")
def edit_match(match_id: str, req: EditMatchRequest, db: Session = Depends(get_db)):
    return ApprovalService.edit_and_approve(
        db,
        match_id=match_id,
        override_activity_id=req.override_activity_id,
        new_progress_percent=req.new_progress_percent,
        new_actual_quantity=req.new_actual_quantity,
        new_status=req.new_status,
        decided_by=req.decided_by,
        notes=req.notes
    )

# 11. Governance: Reject Match
@router.post("/matches/{match_id}/reject")
def reject_match(match_id: str, req: RejectMatchRequest, db: Session = Depends(get_db)):
    return ApprovalService.reject_match(db, match_id, decided_by=req.decided_by, reason=req.reason)

# 12. Dashboard Summary
@router.get("/dashboard/summary")
def get_dashboard_summary(project_id: str = "OIL-DNPE-2026", db: Session = Depends(get_db)):
    return DashboardService.get_summary(db, project_id)

# 13. Audit Trail
@router.get("/audit", response_model=List[AuditLogResponse])
def get_audit_trail(limit: int = 50, db: Session = Depends(get_db)):
    return (
        db.query(AuditLog)
        .order_by(AuditLog.timestamp.desc())
        .limit(limit)
        .all()
    )

# 14. Demo Reset Endpoint
@router.post("/demo/reset")
def reset_demo_scenario(db: Session = Depends(get_db)):
    from scripts.seed_demo import run_seed
    run_seed(db)
    return {"status": "success", "message": "Demo scenario reset successfully to baseline"}

# 15. System Health
@router.get("/health/system")
def get_system_health(db: Session = Depends(get_db)):
    db_ok = True
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_ok = False
        
    return {
        "backend": "healthy",
        "database": "connected" if db_ok else "disconnected",
        "ai_provider": "Hosted Gemini" if settings.AI_PROVIDER == "gemini" and settings.GEMINI_API_KEY else "Deterministic Offline Fallback",
        "embedding_provider": "Local Scikit TF-IDF & Vector Space (Offline-Ready)",
        "demo_mode": True,
        "offline_ready": True
    }
