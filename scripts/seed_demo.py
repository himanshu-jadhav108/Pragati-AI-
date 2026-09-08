import os
import sys
import csv
import json
from datetime import datetime, timedelta

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from sqlalchemy.orm import Session

from backend.app.db.session import engine, SessionLocal, Base
from backend.app.models.entities import (
    Project, WBSNode, Activity, Document, FieldEvent, Match, ProgressUpdate, AuditLog, DelayEvent
)
from backend.app.services.matching.matching_engine import MatchingEngine

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

def run_seed(db: Session = None):
    own_session = False
    if db is None:
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        own_session = True
    else:
        # Clear all existing tables
        db.query(AuditLog).delete()
        db.query(ProgressUpdate).delete()
        db.query(Match).delete()
        db.query(FieldEvent).delete()
        db.query(Document).delete()
        db.query(Activity).delete()
        db.query(WBSNode).delete()
        db.query(Project).delete()
        db.commit()

    print("Seeding PRAGATI AI demo database...")

    # 1. Seed Project
    project = Project(
        id="OIL-DNPE-2026",
        name="Duliajan-Numaligarh Pipeline Expansion (DNPE)",
        description="Crude oil trunk pipeline expansion and pumping station upgrade project",
        start_date="2026-01-01",
        finish_date="2026-12-31",
        planned_progress=68.5,
        actual_progress=54.2
    )
    db.add(project)
    db.commit()

    # 2. Seed WBS Nodes
    wbs_file = os.path.join(DATA_DIR, "wbs.csv")
    if os.path.exists(wbs_file):
        with open(wbs_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                node = WBSNode(
                    wbs_id=r["wbs_id"],
                    name=r["name"],
                    level=int(r["level"]),
                    parent_id=r["parent_id"] if r["parent_id"] else None
                )
                db.add(node)
        db.commit()

    # 3. Seed Activities
    act_file = os.path.join(DATA_DIR, "activities.csv")
    if os.path.exists(act_file):
        with open(act_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                act = Activity(
                    activity_id=r["activity_id"],
                    project_id="OIL-DNPE-2026",
                    wbs_id=r["wbs_id"],
                    description=r["description"],
                    discipline=r["discipline"],
                    location=r["location"],
                    equipment_id=r["equipment_id"],
                    planned_start=r["planned_start"],
                    planned_finish=r["planned_finish"],
                    planned_progress=float(r["planned_progress"]),
                    actual_progress=float(r["actual_progress"]),
                    actual_start=r["actual_start"] if r["actual_start"] else None,
                    actual_finish=r["actual_finish"] if r["actual_finish"] else None,
                    target_quantity=float(r["target_quantity"]),
                    actual_quantity=float(r["actual_quantity"]),
                    unit=r["unit"],
                    status=r["status"]
                )
                db.add(act)
        db.commit()

    # 4. Seed Historical Approved Updates & Audit Logs
    audit_seed_1 = AuditLog(
        event_id="EVT-HIST-001",
        document_id="DPR-OIL-2026-0210.txt",
        match_id="MTH-HIST-001",
        ai_top_activity_id="CIV-L6-0112",
        ai_score=0.94,
        ai_confidence="HIGH",
        action="APPROVE",
        final_activity_id="CIV-L6-0112",
        previous_state={"activity_id": "CIV-L6-0112", "actual_progress": 60.0, "status": "IN_PROGRESS"},
        resulting_state={"activity_id": "CIV-L6-0112", "actual_progress": 100.0, "status": "COMPLETED"},
        actor="Chief Planner",
        timestamp=datetime.utcnow() - timedelta(days=5),
        notes="Approved completed foundation pour for Booster Pump P-101A"
    )
    db.add(audit_seed_1)

    audit_seed_2 = AuditLog(
        event_id="EVT-HIST-002",
        document_id="DPR-OIL-2026-0212.txt",
        match_id="MTH-HIST-002",
        ai_top_activity_id="CIV-L6-0113",
        ai_score=0.91,
        ai_confidence="HIGH",
        action="APPROVE",
        final_activity_id="CIV-L6-0113",
        previous_state={"activity_id": "CIV-L6-0113", "actual_progress": 70.0, "status": "IN_PROGRESS"},
        resulting_state={"activity_id": "CIV-L6-0113", "actual_progress": 100.0, "status": "COMPLETED"},
        actor="Chief Planner",
        timestamp=datetime.utcnow() - timedelta(days=4),
        notes="Approved completed foundation pour for Booster Pump P-101B"
    )
    db.add(audit_seed_2)
    db.commit()

    # 5. Seed Pre-loaded DPR Documents
    dprs_dir = os.path.join(DATA_DIR, "dprs")
    sample_files = [
        "DPR-OIL-2026-0308-01.txt",
        "DPR-OIL-2026-0218-02.txt",
        "DPR-OIL-2026-0302-03.txt",
        "DPR-OIL-2026-0305-04.txt"
    ]

    for fname in sample_files:
        fpath = os.path.join(dprs_dir, fname)
        if os.path.exists(fpath):
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
            doc = Document(
                project_id="OIL-DNPE-2026",
                filename=fname,
                file_type="txt",
                file_size=len(content.encode("utf-8")),
                raw_text=content,
                uploaded_by="Site Engineer"
            )
            db.add(doc)
    db.commit()

    # 6. Extract and Match Ambiguous Case so it's already in the review queue
    ambig_doc = db.query(Document).filter(Document.filename == "DPR-OIL-2026-0218-02.txt").first()
    if ambig_doc:
        from backend.app.services.extraction.extractor import RuleBasedFallbackExtractor
        ext = RuleBasedFallbackExtractor()
        events = ext.extract_events(ambig_doc.raw_text, metadata={"filename": ambig_doc.filename})
        matching_engine = MatchingEngine(db, project_id="OIL-DNPE-2026")
        for e in events:
            fe = FieldEvent(
                document_id=ambig_doc.id,
                raw_text=e.evidence_text or e.activity_description,
                event_date=e.event_date,
                discipline=e.discipline,
                activity_description=e.activity_description,
                location=e.location,
                equipment_id=e.equipment_id,
                status=e.status,
                progress_percent=e.progress_percent,
                quantity=e.quantity,
                unit=e.unit,
                evidence_text=e.evidence_text,
                extraction_provider="deterministic_fallback"
            )
            db.add(fe)
            db.flush()
            matching_engine.process_and_persist_matches(fe)

    # Also extract and match Unmatched Case so it's in the unmatched queue
    unmatch_doc = db.query(Document).filter(Document.filename == "DPR-OIL-2026-0302-03.txt").first()
    if unmatch_doc:
        from backend.app.services.extraction.extractor import RuleBasedFallbackExtractor
        ext = RuleBasedFallbackExtractor()
        events = ext.extract_events(unmatch_doc.raw_text, metadata={"filename": unmatch_doc.filename})
        matching_engine = MatchingEngine(db, project_id="OIL-DNPE-2026")
        for e in events:
            fe = FieldEvent(
                document_id=unmatch_doc.id,
                raw_text=e.evidence_text or e.activity_description,
                event_date=e.event_date,
                discipline=e.discipline,
                activity_description=e.activity_description,
                location=e.location,
                equipment_id=e.equipment_id,
                status=e.status,
                progress_percent=e.progress_percent,
                quantity=e.quantity,
                unit=e.unit,
                evidence_text=e.evidence_text,
                extraction_provider="deterministic_fallback"
            )
            db.add(fe)
            db.flush()
            matching_engine.process_and_persist_matches(fe)

    db.commit()
    print("Seeding completed successfully!")

    if own_session:
        db.close()

if __name__ == "__main__":
    run_seed()
