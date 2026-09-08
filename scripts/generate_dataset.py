"""
PRAGATI AI - Synthetic Dataset Generator
SIH26122 - Oil India Limited
Generates realistic WBS (L1-L6), activities, schedule, DPR documents, and ground truth dataset.
"""

import os
import csv
import json
import random
from datetime import datetime, timedelta

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DPRS_DIR = os.path.join(DATA_DIR, "dprs")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(DPRS_DIR, exist_ok=True)

PROJECT = {
    "id": "OIL-DNPE-2026",
    "name": "Duliajan-Numaligarh Pipeline Expansion (DNPE)",
    "description": "Crude oil trunk pipeline expansion and pumping station upgrade project",
    "start_date": "2026-01-01",
    "finish_date": "2026-12-31",
    "planned_progress": 68.5,
    "actual_progress": 54.2
}

DISCIPLINES = ["Piping", "Civil", "Mechanical", "Electrical", "Instrumentation", "HSE"]

LOCATIONS = [
    "V-105", "V-102", "Pump House PH-1", "Pump House PH-2", "Compressor Shed CS-A",
    "Tank Farm TF-3", "Scraper Station SS-01", "Metering Skid MS-02",
    "Valve Station VS-04", "Control Room CR-1", "Substation SS-2"
]

EQUIPMENT = [
    "V-105", "V-102", "P-101A", "P-101B", "K-201", "TK-301", "TK-302",
    "SK-01", "VS-04", "MOT-101", "FIT-204", "PIT-108"
]

def generate_dataset():
    random.seed(42)
    base_date = datetime(2026, 1, 15)

    # 1. Generate WBS Nodes (L1 to L5)
    wbs_nodes = [
        {"wbs_id": "1", "name": "DNPE Project", "level": 1, "parent_id": None},
        {"wbs_id": "1.1", "name": "Pipeline Trunk Line", "level": 2, "parent_id": "1"},
        {"wbs_id": "1.2", "name": "Pumping Station Upgrades", "level": 2, "parent_id": "1"},
        {"wbs_id": "1.3", "name": "Terminal & Metering Facility", "level": 2, "parent_id": "1"},
        
        # Sub-WBS L3
        {"wbs_id": "1.1.1", "name": "Right of Way & Trenching", "level": 3, "parent_id": "1.1"},
        {"wbs_id": "1.1.2", "name": "Mainline Piping & Welding", "level": 3, "parent_id": "1.1"},
        {"wbs_id": "1.1.3", "name": "Crossing & Valve Stations", "level": 3, "parent_id": "1.1"},
        {"wbs_id": "1.2.1", "name": "PH-1 Civil Foundations", "level": 3, "parent_id": "1.2"},
        {"wbs_id": "1.2.2", "name": "PH-1 Mechanical Equipment", "level": 3, "parent_id": "1.2"},
        {"wbs_id": "1.2.3", "name": "PH-1 Piping & Spooling", "level": 3, "parent_id": "1.2"},
        {"wbs_id": "1.2.4", "name": "Electrical & Instrumentation", "level": 3, "parent_id": "1.2"},
        {"wbs_id": "1.3.1", "name": "Metering Skids & Manifolds", "level": 3, "parent_id": "1.3"},
        {"wbs_id": "1.3.2", "name": "Storage Tanks & Dykes", "level": 3, "parent_id": "1.3"},

        # Sub-WBS L4 & L5
        {"wbs_id": "1.2.3.1", "name": "High Pressure Piping Systems", "level": 4, "parent_id": "1.2.3"},
        {"wbs_id": "1.2.3.1.1", "name": "Section 24-inch Spool Erection", "level": 5, "parent_id": "1.2.3.1"},
        {"wbs_id": "1.2.3.1.2", "name": "Section 16-inch Suction Piping", "level": 5, "parent_id": "1.2.3.1"},
        {"wbs_id": "1.2.1.1", "name": "Equipment Foundation Concrete", "level": 4, "parent_id": "1.2.1"},
        {"wbs_id": "1.2.1.1.1", "name": "Heavy Pump Foundations", "level": 5, "parent_id": "1.2.1.1"},
        {"wbs_id": "1.2.4.1", "name": "Field Instruments Installation", "level": 4, "parent_id": "1.2.4"},
        {"wbs_id": "1.2.4.1.1", "name": "Pressure & Flow Transmitters", "level": 5, "parent_id": "1.2.4.1"}
    ]

    # Save WBS CSV
    wbs_file = os.path.join(DATA_DIR, "wbs.csv")
    with open(wbs_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["wbs_id", "name", "level", "parent_id"])
        writer.writeheader()
        writer.writerows(wbs_nodes)

    # 2. Generate Activities (L5 / L6) - target ~200 activities
    activities = []
    
    # Hero activity explicitly defined
    hero_activity = {
        "activity_id": "PIP-L6-0427",
        "wbs_id": "1.2.3.1.1",
        "description": "Erect Line 24-inch near V-105",
        "discipline": "Piping",
        "location": "V-105",
        "equipment_id": "V-105",
        "planned_start": "2026-03-01",
        "planned_finish": "2026-03-15",
        "planned_progress": 100.0,
        "actual_progress": 0.0,
        "actual_start": None,
        "actual_finish": None,
        "target_quantity": 14.0,
        "actual_quantity": 0.0,
        "unit": "spools",
        "status": "NOT_STARTED"
    }
    activities.append(hero_activity)

    # Ambiguous Pair 1: PIP-L6-0501 and PIP-L6-0502 (same action, different equipment/loc)
    activities.append({
        "activity_id": "PIP-L6-0501",
        "wbs_id": "1.2.3.1.2",
        "description": "Fit-up and weld 16-inch suction line at Pump P-101A",
        "discipline": "Piping",
        "location": "Pump House PH-1",
        "equipment_id": "P-101A",
        "planned_start": "2026-02-10",
        "planned_finish": "2026-02-25",
        "planned_progress": 100.0,
        "actual_progress": 50.0,
        "actual_start": "2026-02-11",
        "actual_finish": None,
        "target_quantity": 8.0,
        "actual_quantity": 4.0,
        "unit": "joints",
        "status": "IN_PROGRESS"
    })
    activities.append({
        "activity_id": "PIP-L6-0502",
        "wbs_id": "1.2.3.1.2",
        "description": "Fit-up and weld 16-inch suction line at Pump P-101B",
        "discipline": "Piping",
        "location": "Pump House PH-1",
        "equipment_id": "P-101B",
        "planned_start": "2026-02-15",
        "planned_finish": "2026-03-02",
        "planned_progress": 100.0,
        "actual_progress": 0.0,
        "actual_start": None,
        "actual_finish": None,
        "target_quantity": 8.0,
        "actual_quantity": 0.0,
        "unit": "joints",
        "status": "NOT_STARTED"
    })

    # Ambiguous Pair 2: Civil foundations in adjacent locations
    activities.append({
        "activity_id": "CIV-L6-0112",
        "wbs_id": "1.2.1.1.1",
        "description": "Pour RCC foundation for Booster Pump P-101A",
        "discipline": "Civil",
        "location": "Pump House PH-1",
        "equipment_id": "P-101A",
        "planned_start": "2026-01-20",
        "planned_finish": "2026-02-05",
        "planned_progress": 100.0,
        "actual_progress": 100.0,
        "actual_start": "2026-01-22",
        "actual_finish": "2026-02-04",
        "target_quantity": 45.0,
        "actual_quantity": 45.0,
        "unit": "cum",
        "status": "COMPLETED"
    })
    activities.append({
        "activity_id": "CIV-L6-0113",
        "wbs_id": "1.2.1.1.1",
        "description": "Pour RCC foundation for Booster Pump P-101B",
        "discipline": "Civil",
        "location": "Pump House PH-1",
        "equipment_id": "P-101B",
        "planned_start": "2026-01-25",
        "planned_finish": "2026-02-10",
        "planned_progress": 100.0,
        "actual_progress": 100.0,
        "actual_start": "2026-01-27",
        "actual_finish": "2026-02-09",
        "target_quantity": 45.0,
        "actual_quantity": 45.0,
        "unit": "cum",
        "status": "COMPLETED"
    })

    # Generate 190 more realistic activities
    templates = [
        ("Piping", "Hydrostatic testing of Line {size} near {loc}", "joints", 10, 50, "1.2.3.1"),
        ("Piping", "Erection and torqueing of flange joints on {eq}", "joints", 4, 24, "1.2.3.1.2"),
        ("Piping", "Installation of 24-inch tie-in spool at {loc}", "spools", 2, 10, "1.2.3.1.1"),
        ("Piping", "Field weld fit-up on {eq} header line", "joints", 6, 20, "1.2.3.1"),
        ("Civil", "Excavation and backfilling for pipeline trench at {loc}", "m", 50, 500, "1.1.1"),
        ("Civil", "Construction of RCC valve pit enclosure at {loc}", "units", 1, 3, "1.1.3"),
        ("Civil", "Placing rebar reinforcement for equipment pad {eq}", "tonnes", 5, 30, "1.2.1.1"),
        ("Civil", "Cable trench concrete lining works at {loc}", "m", 20, 200, "1.2.1"),
        ("Mechanical", "Alignment and leveling of centrifugal pump {eq}", "units", 1, 2, "1.2.2"),
        ("Mechanical", "Installation of pig launcher barrel at {loc}", "units", 1, 1, "1.1.3"),
        ("Mechanical", "Mounting of electric drive motor on {eq}", "units", 1, 2, "1.2.2"),
        ("Mechanical", "Internal inspection and boxing up of vessel {eq}", "units", 1, 1, "1.3.2"),
        ("Electrical", "Laying 11kV HT power cable from {loc} to {eq}", "m", 100, 1200, "1.2.4"),
        ("Electrical", "Earthing grid copper strip laying and bonding at {loc}", "m", 50, 400, "1.2.4"),
        ("Electrical", "Installation of Motor Control Center MCC panel at {loc}", "panels", 2, 8, "1.2.4"),
        ("Instrumentation", "Mounting and impulse tubing for transmitter {eq}", "transmitters", 2, 12, "1.2.4.1.1"),
        ("Instrumentation", "Calibration and loop check of flow sensor on {loc}", "loops", 1, 6, "1.2.4.1.1"),
        ("Instrumentation", "Installation of ESD safety shutdown valve at {loc}", "valves", 1, 4, "1.2.4.1"),
        ("HSE", "Radiography safety barricading and clearing for NDT at {loc}", "shifts", 5, 20, "1.1.2"),
        ("HSE", "Hydrotesting environmental containment setup at {loc}", "checkpoints", 2, 6, "1.2.3.1")
    ]

    counter = 1000
    for disc, desc_tpl, unit, qmin, qmax, wbs_node in templates:
        for loc in LOCATIONS[:8]:
            counter += 1
            eq = random.choice(EQUIPMENT)
            size = random.choice(["8-inch", "12-inch", "16-inch", "24-inch", "30-inch"])
            desc = desc_tpl.format(loc=loc, eq=eq, size=size)
            
            p_start = base_date + timedelta(days=random.randint(0, 75))
            duration = random.randint(7, 28)
            p_finish = p_start + timedelta(days=duration)
            target_q = float(random.randint(qmin, qmax))
            
            # Progress state
            if p_finish < datetime(2026, 2, 28):
                status = "COMPLETED"
                p_progress = 100.0
                act_progress = 100.0
                act_q = target_q
                a_start = (p_start + timedelta(days=random.randint(-2, 3))).strftime("%Y-%m-%d")
                a_finish = (p_finish + timedelta(days=random.randint(-1, 5))).strftime("%Y-%m-%d")
            elif p_start <= datetime(2026, 3, 5):
                status = "IN_PROGRESS"
                p_progress = round(random.uniform(40.0, 85.0), 1)
                act_progress = round(p_progress * random.uniform(0.6, 0.95), 1)
                act_q = round(target_q * (act_progress / 100.0), 1)
                a_start = p_start.strftime("%Y-%m-%d")
                a_finish = None
            else:
                status = "NOT_STARTED"
                p_progress = round(random.uniform(10.0, 30.0), 1)
                act_progress = 0.0
                act_q = 0.0
                a_start = None
                a_finish = None

            prefix = disc[:3].upper()
            act_id = f"{prefix}-L6-{counter}"

            activities.append({
                "activity_id": act_id,
                "wbs_id": wbs_node,
                "description": desc,
                "discipline": disc,
                "location": loc,
                "equipment_id": eq,
                "planned_start": p_start.strftime("%Y-%m-%d"),
                "planned_finish": p_finish.strftime("%Y-%m-%d"),
                "planned_progress": p_progress,
                "actual_progress": act_progress,
                "actual_start": a_start,
                "actual_finish": a_finish,
                "target_quantity": target_q,
                "actual_quantity": act_q,
                "unit": unit,
                "status": status
            })

    # Save Activities CSV
    act_file = os.path.join(DATA_DIR, "activities.csv")
    with open(act_file, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "activity_id", "wbs_id", "description", "discipline", "location",
            "equipment_id", "planned_start", "planned_finish", "planned_progress",
            "actual_progress", "actual_start", "actual_finish", "target_quantity",
            "actual_quantity", "unit", "status"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(activities)

    # Save Schedule CSV (alias friendly)
    schedule_file = os.path.join(DATA_DIR, "schedule.csv")
    with open(schedule_file, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "Activity_ID", "WBS", "Activity_Description", "Discipline", "Location",
            "Equipment", "Planned_Start", "Planned_Finish", "Planned_Progress",
            "Actual_Progress", "Status"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for a in activities:
            writer.writerow({
                "Activity_ID": a["activity_id"],
                "WBS": a["wbs_id"],
                "Activity_Description": a["description"],
                "Discipline": a["discipline"],
                "Location": a["location"],
                "Equipment": a["equipment_id"],
                "Planned_Start": a["planned_start"],
                "Planned_Finish": a["planned_finish"],
                "Planned_Progress": a["planned_progress"],
                "Actual_Progress": a["actual_progress"],
                "Status": a["status"]
            })

    # 3. Create Ground Truth and DPR Documents
    ground_truth = []
    
    # Hero DPR
    hero_dpr_text = """OIL INDIA LIMITED - DAILY PROGRESS REPORT (DPR)
Project: Duliajan-Numaligarh Pipeline Expansion (DNPE)
Date: 2026-03-08
Report Ref: DPR-OIL-2026-0308-01
Site Engineer: D. Borah
Area: Pumping Station Upgrades / Vessel Yard

FIELD ACTIVITY LOG:
1. Spool erection near V-105 completed today. 14 spools installed.
2. Hydrotesting pre-checks initiated on drain manifolds.
3. Zero safety incidents reported during crane lifting operations.
"""
    hero_path = os.path.join(DPRS_DIR, "DPR-OIL-2026-0308-01.txt")
    with open(hero_path, "w", encoding="utf-8") as f:
        f.write(hero_dpr_text)

    ground_truth.append({
        "event_id": "EVT-HERO-001",
        "doc_filename": "DPR-OIL-2026-0308-01.txt",
        "raw_text": "Spool erection near V-105 completed today. 14 spools installed.",
        "expected_activity_id": "PIP-L6-0427",
        "expected_confidence": "HIGH",
        "expected_discipline": "Piping",
        "expected_location": "V-105",
        "expected_quantity": 14.0,
        "expected_unit": "spools",
        "expected_status": "COMPLETED",
        "scenario": "HERO_SUCCESS"
    })

    # Ambiguous DPR
    ambig_dpr_text = """OIL INDIA LIMITED - DAILY PROGRESS REPORT (DPR)
Project: Duliajan-Numaligarh Pipeline Expansion (DNPE)
Date: 2026-02-18
Report Ref: DPR-OIL-2026-0218-02
Site Engineer: R. Gogoi
Area: Pump House PH-1

FIELD ACTIVITY LOG:
1. Suction line welding in progress at Pump House PH-1. Completed fit-up and weld for 4 joints today.
2. Foundation grouting ongoing at adjacent compressor bay.
"""
    ambig_path = os.path.join(DPRS_DIR, "DPR-OIL-2026-0218-02.txt")
    with open(ambig_path, "w", encoding="utf-8") as f:
        f.write(ambig_dpr_text)

    ground_truth.append({
        "event_id": "EVT-AMBIG-002",
        "doc_filename": "DPR-OIL-2026-0218-02.txt",
        "raw_text": "Suction line welding in progress at Pump House PH-1. Completed fit-up and weld for 4 joints today.",
        "expected_activity_id": "PIP-L6-0501",  # or PIP-L6-0502 (both plausible)
        "expected_confidence": "MEDIUM",
        "expected_discipline": "Piping",
        "expected_location": "Pump House PH-1",
        "expected_quantity": 4.0,
        "expected_unit": "joints",
        "expected_status": "IN_PROGRESS",
        "scenario": "AMBIGUOUS_CHOICE"
    })

    # Unmatched DPR
    unmatch_dpr_text = """OIL INDIA LIMITED - DAILY PROGRESS REPORT (DPR)
Project: Duliajan-Numaligarh Pipeline Expansion (DNPE)
Date: 2026-03-02
Report Ref: DPR-OIL-2026-0302-03
Site Security & Admin: K. Sharma
Area: Main Gate & Camp Perimeter

DAILY LOG:
1. Catering supply van arrived at main gate 3 with provisions for the worker mess.
2. Security perimeter solar lighting inspection completed without issues.
"""
    unmatch_path = os.path.join(DPRS_DIR, "DPR-OIL-2026-0302-03.txt")
    with open(unmatch_path, "w", encoding="utf-8") as f:
        f.write(unmatch_dpr_text)

    ground_truth.append({
        "event_id": "EVT-UNMATCH-003",
        "doc_filename": "DPR-OIL-2026-0302-03.txt",
        "raw_text": "Catering supply van arrived at main gate 3 with provisions for the worker mess.",
        "expected_activity_id": None,
        "expected_confidence": "UNMATCHED",
        "expected_discipline": None,
        "expected_location": "main gate 3",
        "expected_quantity": None,
        "expected_unit": None,
        "expected_status": "UNKNOWN",
        "scenario": "NO_MATCH"
    })

    # Synonym phrasing case
    synonym_dpr_text = """OIL INDIA LIMITED - DAILY PROGRESS REPORT (DPR)
Project: Duliajan-Numaligarh Pipeline Expansion (DNPE)
Date: 2026-03-05
Report Ref: DPR-OIL-2026-0305-04
Site Engineer: S. Hazarika
Area: Station 2 Valve Yard

FIELD ACTIVITY LOG:
1. High pressure piping spool installation done near V-105. All 14 pieces mounted and bolted.
"""
    synonym_path = os.path.join(DPRS_DIR, "DPR-OIL-2026-0305-04.txt")
    with open(synonym_path, "w", encoding="utf-8") as f:
        f.write(synonym_dpr_text)

    ground_truth.append({
        "event_id": "EVT-SYNONYM-004",
        "doc_filename": "DPR-OIL-2026-0305-04.txt",
        "raw_text": "High pressure piping spool installation done near V-105. All 14 pieces mounted and bolted.",
        "expected_activity_id": "PIP-L6-0427",
        "expected_confidence": "HIGH",
        "expected_discipline": "Piping",
        "expected_location": "V-105",
        "expected_quantity": 14.0,
        "expected_unit": "pieces",
        "expected_status": "COMPLETED",
        "scenario": "SYNONYM_PHRASING"
    })

    # Save ground truth CSV
    gt_file = os.path.join(DATA_DIR, "ground_truth.csv")
    with open(gt_file, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "event_id", "doc_filename", "raw_text", "expected_activity_id",
            "expected_confidence", "expected_discipline", "expected_location",
            "expected_quantity", "expected_unit", "expected_status", "scenario"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(ground_truth)

    # Save Project JSON
    with open(os.path.join(DATA_DIR, "project.json"), "w", encoding="utf-8") as f:
        json.dump(PROJECT, f, indent=2)

    print(f"Generated dataset successfully:")
    print(f"- WBS Nodes: {len(wbs_nodes)}")
    print(f"- Activities: {len(activities)}")
    print(f"- Sample DPRs: {len(ground_truth)}")
    print(f"- Output directory: {DATA_DIR}")

if __name__ == "__main__":
    generate_dataset()
