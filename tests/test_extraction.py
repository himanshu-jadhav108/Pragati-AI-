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

def test_full_dpr_with_headers_ignores_metadata():
    extractor = RuleBasedFallbackExtractor()
    text = """OIL INDIA LIMITED - DAILY PROGRESS REPORT (DPR)
Project: Duliajan-Numaligarh Pipeline Expansion (DNPE)
Date: 2026-03-08
Report Ref: DPR-OIL-2026-0308-01
Site Engineer: D. Borah
Area: Pumping Station Upgrades / Vessel Yard

FIELD ACTIVITY LOG:
1. 24-inch spool erected near V-105 today. 14 spools installed.
2. Hydrotesting pre-checks initiated on drain manifolds.

DAILY LOG:
Site Security & Admin: K. Sharma
3. Foundation concrete poured at Pump House PH-2. 45.5 cum completed.
"""
    events = extractor.extract_events(text)
    # Must extract the engineering statements, but NOT headers or admin lines
    descriptions = [e.activity_description for e in events]
    for desc in descriptions:
        assert "FIELD ACTIVITY LOG" not in desc
        assert "DAILY LOG" not in desc
        assert "Site Engineer" not in desc
        assert "Report Ref" not in desc
        assert "Site Security" not in desc

    assert len(events) == 3
    # Check that decimal quantity was parsed accurately
    conc_evt = next((e for e in events if "concrete" in e.activity_description.lower()), None)
    assert conc_evt is not None
    assert conc_evt.quantity == 45.5
    assert conc_evt.unit == "cum"

def test_unknown_and_varied_units_extraction():
    extractor = RuleBasedFallbackExtractor()
    cases = [
        ("Installed 12 brackets on column C-4.", 12.0, "brackets"),
        ("Erected 8 pipe supports along rack B.", 8.0, "supports"),
        ("Pulled 150 meters power cable.", 150.0, "meters"),
        ("Terminated 4 control panels in substation.", 4.0, "panels"),
        ("Installed 6 check valves on header.", 6.0, "valves"),
        ("Replaced 10 pieces flange gaskets.", 10.0, "pieces"),
        ("Assembled 15 widgets near skid.", 15.0, "widgets"),
        ("Completed 5 without units today.", 5.0, None),
    ]
    for text, expected_qty, expected_unit in cases:
        events = extractor.extract_events(text)
        assert len(events) == 1, f"Failed to extract single event from: {text}"
        evt = events[0]
        assert evt.quantity == expected_qty, f"Qty mismatch for: {text}"
        if expected_unit is not None:
            assert evt.unit == expected_unit, f"Unit mismatch for: {text}"

def test_deterministic_demo_date_resolution():
    extractor = RuleBasedFallbackExtractor()
    events_today = extractor.extract_events("24-inch spool erected near V-105 today.")
    assert len(events_today) == 1
    assert events_today[0].event_date == "2026-03-08"

    events_yesterday = extractor.extract_events("Foundations completed yesterday near PH-1.")
    assert len(events_yesterday) == 1
    assert events_yesterday[0].event_date == "2026-03-07"

