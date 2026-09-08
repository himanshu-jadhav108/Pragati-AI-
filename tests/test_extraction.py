import pytest
from backend.app.services.extraction.extractor import RuleBasedFallbackExtractor
from backend.app.schemas.schemas import FieldEventExtract

def test_hero_dpr_extraction():
    extractor = RuleBasedFallbackExtractor()
    text = "Spool erection near V-105 completed today. 14 spools installed."
    events = extractor.extract_events(text, metadata={"date": "2026-03-08", "filename": "test_dpr.txt"})
    
    assert len(events) == 1
    evt = events[0]
    assert isinstance(evt, FieldEventExtract)
    assert evt.discipline == "Piping"
    assert evt.location == "V-105"
    assert evt.equipment_id == "V-105"
    assert evt.status == "COMPLETED"
    assert evt.quantity == 14.0
    assert evt.unit == "spools"
    assert evt.event_date == "2026-03-08"
    assert "14 spools installed" in evt.evidence_text

def test_ambiguous_dpr_extraction():
    extractor = RuleBasedFallbackExtractor()
    text = "Suction line welding in progress at Pump House PH-1. Completed fit-up and weld for 4 joints today."
    events = extractor.extract_events(text, metadata={"date": "2026-02-18"})
    
    assert len(events) == 1
    evt = events[0]
    assert evt.discipline == "Piping"
    assert evt.location == "Pump House PH-1"
    assert evt.quantity == 4.0
    assert evt.unit == "joints"

def test_unmatched_dpr_extraction():
    extractor = RuleBasedFallbackExtractor()
    text = "Catering supply van arrived at main gate 3 with provisions for the worker mess."
    events = extractor.extract_events(text, metadata={"date": "2026-03-02"})
    
    assert len(events) == 1
    evt = events[0]
    # Should not invent piping or civil discipline
    assert evt.discipline is None
    assert evt.quantity is None
