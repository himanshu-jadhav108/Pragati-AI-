import io
import csv
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from backend.app.models.entities import Activity, Project, WBSNode

COLUMN_ALIASES = {
    "activity_id": ["activity id", "activity_id", "act_id", "activity code", "id"],
    "description": ["description", "activity description", "activity_description", "task name", "activity name"],
    "discipline": ["discipline", "disc", "department", "trade"],
    "wbs_id": ["wbs", "wbs id", "wbs_id", "wbs code"],
    "location": ["location", "area", "site", "loc"],
    "equipment_id": ["equipment", "equipment_id", "equipment id", "tag", "tag no"],
    "planned_start": ["planned start", "planned_start", "start date", "target start"],
    "planned_finish": ["planned finish", "planned_finish", "finish date", "target finish"],
    "planned_progress": ["planned progress", "planned_progress", "plan %", "planned %", "target progress"],
    "actual_progress": ["actual progress", "actual_progress", "act %", "actual %"],
    "target_quantity": ["target quantity", "target_quantity", "quantity", "qty", "scope"],
    "unit": ["unit", "uom", "measurement unit"],
    "status": ["status", "activity status", "state"]
}

def normalize_header(header: str) -> str:
    cleaned = header.strip().lower().replace("_", " ")
    for standard_col, aliases in COLUMN_ALIASES.items():
        if cleaned == standard_col.replace("_", " ") or cleaned in aliases:
            return standard_col
    return cleaned

def parse_float(val: Any, default: float = 0.0) -> float:
    if val is None:
        return default
    s = str(val).strip().rstrip("%")
    try:
        f = float(s)
        if f <= 1.0 and f > 0.0 and "%" in str(val):
            return f * 100.0
        return f
    except ValueError:
        return default

def parse_date_str(val: Any) -> str:
    if not val:
        return ""
    s = str(val).strip()
    for fmt in ["%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"]:
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return s[:10]

def parse_xlsx_data(file_bytes: bytes) -> List[Dict[str, Any]]:
    """Parse XLSX without openpyxl using built-in zipfile and XML parser."""
    zf = zipfile.ZipFile(io.BytesIO(file_bytes))
    
    # 1. Read shared strings
    shared_strings = []
    if "xl/sharedStrings.xml" in zf.namelist():
        xml_content = zf.read("xl/sharedStrings.xml")
        root = ET.fromstring(xml_content)
        for si in root.findall("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si"):
            t = si.find("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t")
            shared_strings.append(t.text if t is not None and t.text is not None else "")
            
    # 2. Read sheet1.xml
    sheet_name = "xl/worksheets/sheet1.xml"
    if sheet_name not in zf.namelist():
        # Fallback to first worksheet found
        sheets = [n for n in zf.namelist() if n.startswith("xl/worksheets/sheet")]
        if not sheets:
            raise ValueError("No worksheets found in XLSX file")
        sheet_name = sheets[0]
        
    xml_content = zf.read(sheet_name)
    root = ET.fromstring(xml_content)
    
    rows = []
    ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    sheet_data = root.find(f"{ns}sheetData")
    if sheet_data is None:
        return []
        
    for row in sheet_data.findall(f"{ns}row"):
        current_row = []
        for cell in row.findall(f"{ns}c"):
            t_attr = cell.get("t")
            val_elem = cell.find(f"{ns}v")
            if val_elem is None or val_elem.text is None:
                current_row.append("")
                continue
            val = val_elem.text
            if t_attr == "s":
                idx = int(val)
                val = shared_strings[idx] if idx < len(shared_strings) else ""
            current_row.append(val)
        if current_row:
            rows.append(current_row)
            
    if not rows:
        return []
        
    headers = [normalize_header(str(c)) for c in rows[0]]
    result = []
    for r in rows[1:]:
        row_dict = {}
        for idx, h in enumerate(headers):
            row_dict[h] = r[idx] if idx < len(r) else ""
        result.append(row_dict)
    return result

def parse_csv_data(file_content: str) -> List[Dict[str, Any]]:
    reader = csv.reader(io.StringIO(file_content))
    headers_raw = next(reader, None)
    if not headers_raw:
        return []
    headers = [normalize_header(h) for h in headers_raw]
    
    result = []
    for r in reader:
        if not any(r):
            continue
        row_dict = {}
        for idx, h in enumerate(headers):
            row_dict[h] = r[idx].strip() if idx < len(r) else ""
        result.append(row_dict)
    return result

def import_schedule_to_db(db: Session, project_id: str, raw_rows: List[Dict[str, Any]]) -> Tuple[int, List[str]]:
    imported = 0
    errors = []
    
    for idx, row in enumerate(raw_rows):
        row_num = idx + 2
        act_id = row.get("activity_id")
        desc = row.get("description")
        
        if not act_id or not desc:
            errors.append(f"Row {row_num}: Missing Activity ID or Description")
            continue
            
        discipline = row.get("discipline") or "General"
        location = row.get("location")
        equipment_id = row.get("equipment_id")
        wbs_id = row.get("wbs_id")
        
        planned_start = parse_date_str(row.get("planned_start"))
        planned_finish = parse_date_str(row.get("planned_finish"))
        planned_progress = min(100.0, max(0.0, parse_float(row.get("planned_progress"))))
        actual_progress = min(100.0, max(0.0, parse_float(row.get("actual_progress"))))
        target_qty = parse_float(row.get("target_quantity"))
        unit = row.get("unit") or ""
        status = row.get("status") or ("COMPLETED" if actual_progress >= 100 else ("IN_PROGRESS" if actual_progress > 0 else "NOT_STARTED"))
        
        # Check if activity exists, update or create
        existing = db.query(Activity).filter(Activity.activity_id == act_id).first()
        if existing:
            existing.description = desc
            existing.discipline = discipline
            existing.location = location
            existing.equipment_id = equipment_id
            existing.wbs_id = wbs_id
            existing.planned_start = planned_start
            existing.planned_finish = planned_finish
            existing.planned_progress = planned_progress
            existing.actual_progress = actual_progress
            existing.target_quantity = target_qty
            existing.unit = unit
            existing.status = status
        else:
            new_act = Activity(
                activity_id=act_id,
                project_id=project_id,
                wbs_id=wbs_id,
                description=desc,
                discipline=discipline,
                location=location,
                equipment_id=equipment_id,
                planned_start=planned_start,
                planned_finish=planned_finish,
                planned_progress=planned_progress,
                actual_progress=actual_progress,
                target_quantity=target_qty,
                actual_quantity=0.0,
                unit=unit,
                status=status
            )
            db.add(new_act)
        imported += 1

    db.commit()
    return imported, errors
