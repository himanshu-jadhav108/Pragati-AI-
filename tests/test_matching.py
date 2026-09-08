import pytest
from backend.app.db.session import SessionLocal
from backend.app.services.extraction.extractor import RuleBasedFallbackExtractor
from backend.app.services.matching.matching_engine import MatchingEngine
from backend.app.models.entities import Activity

@pytest.fixture
def db_session():
    db = SessionLocal()
    yield db
    db.close()

def test_hero_case_matching_naturally(db_session):
    extractor = RuleBasedFallbackExtractor()
    engine = MatchingEngine(db_session, project_id="OIL-DNPE-2026")
    
    text = "Spool erection near V-105 completed today. 14 spools installed."
    events = extractor.extract_events(text, metadata={"date": "2026-03-08", "filename": "hero_dpr.txt"})
    assert len(events) == 1
    
    top_candidates, confidence = engine.score_event(events[0])
    
    # Must rank #1 without being hardcoded
    assert len(top_candidates) >= 1
    rank1 = top_candidates[0]
    assert rank1.activity_id == "PIP-L6-0427"
    assert confidence == "HIGH"
    assert rank1.scores.final_score >= 0.70
    assert rank1.scores.score_location == 1.0
    assert rank1.scores.score_entity == 1.0
    assert rank1.scores.score_discipline == 1.0

def test_ambiguous_case_matching(db_session):
    extractor = RuleBasedFallbackExtractor()
    engine = MatchingEngine(db_session, project_id="OIL-DNPE-2026")
    
    text = "Suction line welding in progress at Pump House PH-1. Completed fit-up and weld for 4 joints today."
    events = extractor.extract_events(text, metadata={"date": "2026-02-18", "filename": "ambig_dpr.txt"})
    top_candidates, confidence = engine.score_event(events[0])
    
    assert confidence in ["MEDIUM", "LOW"]
    top_ids = [c.activity_id for c in top_candidates[:2]]
    assert "PIP-L6-0501" in top_ids or "PIP-L6-0502" in top_ids

def test_unmatched_case_logic(db_session):
    extractor = RuleBasedFallbackExtractor()
    engine = MatchingEngine(db_session, project_id="OIL-DNPE-2026")
    
    text = "Catering supply van arrived at main gate 3 with provisions for the worker mess."
    events = extractor.extract_events(text, metadata={"date": "2026-03-02", "filename": "unmatch.txt"})
    top_candidates, confidence = engine.score_event(events[0])
    
    assert confidence == "UNMATCHED"
    if top_candidates:
        assert top_candidates[0].scores.final_score < 0.32

def test_contradiction_penalty(db_session):
    engine = MatchingEngine(db_session, project_id="OIL-DNPE-2026")
    
    # Mock event at V-105
    class MockEvent:
        raw_text = "Spool erection near V-105 completed today."
        evidence_text = raw_text
        activity_description = raw_text
        discipline = "Piping"
        location = "V-105"
        equipment_id = "V-105"
        event_date = "2026-03-08"

    # Activity at Tank Farm (clash)
    act_clash = Activity(
        activity_id="PIP-TEST-999",
        description="Erection at Tank Farm TF-3",
        discipline="Piping",
        location="Tank Farm TF-3",
        equipment_id="TK-301",
        planned_start="2026-03-01",
        planned_finish="2026-03-15",
        actual_progress=0.0,
        status="NOT_STARTED"
    )
    
    penalty, reason = engine._detect_contradictions(MockEvent(), act_clash)
    assert penalty > 0.0
    assert "Location conflict" in reason
