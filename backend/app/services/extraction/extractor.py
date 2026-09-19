import re
import json
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from backend.app.schemas.schemas import FieldEventExtract
from backend.app.core.config import settings

class LLMExtractor(ABC):
    @abstractmethod
    def extract_events(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[FieldEventExtract]:
        pass

class RuleBasedFallbackExtractor(LLMExtractor):
    """
    Deterministic NLP & Rule-Based Field Event Extractor.
    Guarantees 100% offline functionality without external LLM keys.
    Extracts structured events strictly grounded in the evidence.
    """

    DISCIPLINE_KEYWORDS = {
        "Piping": ["spool", "piping", "line", "weld", "fit-up", "flange", "valve", "hydrotest", "suction"],
        "Civil": ["foundation", "concrete", "rcc", "rebar", "excavation", "trench", "backfill", "pad", "grout"],
        "Mechanical": ["pump", "compressor", "motor", "alignment", "launcher", "vessel", "skid", "leveling"],
        "Electrical": ["cable", "ht power", "earthing", "mcc", "panel", "substation", "lighting"],
        "Instrumentation": ["transmitter", "flow sensor", "impulse tubing", "loop check", "esd", "calibration"],
        "HSE": ["safety", "radiography", "barricading", "ndt", "incident", "ppe", "containment"]
    }

    LOCATION_PATTERNS = [
        r"\b(V\-\d{3})\b",
        r"\b(Pump House\s+PH\-\d+)\b",
        r"\b(Compressor Shed\s+CS\-[A-Z0-9]+)\b",
        r"\b(Tank Farm\s+TF\-\d+)\b",
        r"\b(Control Room\s+CR\-\d+)\b",
        r"\b(Valve Station\s+VS\-\d+)\b",
        r"\b(gate\s+\d+)\b",
        r"(?:near|at|in|area)\s+([A-Z0-9\-]+)"
    ]

    EQUIPMENT_PATTERNS = [
        r"\b(V\-\d{3})\b",
        r"\b(P\-\d{3}[A-Z]?)\b",
        r"\b(K\-\d{3})\b",
        r"\b(TK\-\d{3})\b",
        r"\b(SK\-\d{2})\b",
        r"\b(MOT\-\d{3})\b",
        r"\b(FIT\-\d{3})\b",
        r"\b(PIT\-\d{3})\b"
    ]

    STATUS_KEYWORDS = {
        "COMPLETED": ["completed", "done", "finished", "installed", "erected", "mounted", "bolted", "boxed up"],
        "IN_PROGRESS": ["in progress", "ongoing", "started", "initiated", "underway", "welding", "laying", "pouring"],
        "NOT_STARTED": ["planned", "pending", "scheduled"]
    }

    def extract_events(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[FieldEventExtract]:
        metadata = metadata or {}
        doc_date = metadata.get("date")
        
    METADATA_HEADER_PREFIXES = (
        "oil india", "project:", "report ref:", "site engineer:", "site security & admin:",
        "site security and admin:", "area:", "weather:", "shift:", "date:", "daily progress report",
        "prepared by:", "reviewed by:", "approved by:", "contractor:", "distribution:"
    )

    SECTION_HEADER_EXACT = {
        "field activity log:", "daily log:", "site security & admin:", "site security and admin:",
        "general notes:", "observations:", "summary:", "activity log:", "progress summary:"
    }

    KNOWN_UNITS = {
        "spools", "spool", "joints", "joint", "cum", "cu.m", "m3", "m",
        "units", "unit", "meters", "meter", "panels", "panel", "loops",
        "loop", "valves", "valve", "pieces", "piece", "tonnes", "tonne",
        "brackets", "bracket", "supports", "support", "checkpoints", "nos", "no"
    }

    QUANTITY_STOP_WORDS = {
        "hours", "days", "shifts", "am", "pm", "today", "yesterday", "completed",
        "installed", "erected", "started", "done", "near", "at", "in", "the", "with",
        "of", "and", "for", "to", "by", "on", "from"
    }

    def _is_header_or_metadata(self, raw_line: str, cleaned_line: str) -> bool:
        low = cleaned_line.strip().lower()
        if not low:
            return True

        # Exact section headers
        if low in self.SECTION_HEADER_EXACT or low.rstrip(":") in [s.rstrip(":") for s in self.SECTION_HEADER_EXACT]:
            return True

        # Ends with colon and has no digits/quantities or action indicators (pure header)
        if low.endswith(":") and not re.search(r"\d", low):
            return True

        # Starts with any known metadata label
        if any(low.startswith(prefix) for prefix in self.METADATA_HEADER_PREFIXES):
            return True

        # Pure label: value metadata pattern (e.g. "Site Engineer: K. Sharma")
        if re.match(r"^[a-zA-Z\s&]{3,25}:\s*[^:]+$", cleaned_line.strip()):
            label = cleaned_line.split(":", 1)[0].strip().lower()
            if label in {"site engineer", "site security & admin", "site security and admin", "project", "report ref", "area", "weather", "shift", "date"}:
                return True

        return False

    def extract_events(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[FieldEventExtract]:
        metadata = metadata or {}
        doc_date = metadata.get("date")
        
        # Try to parse date from document header if present
        date_match = re.search(r"Date:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})", text, re.IGNORECASE)
        if date_match:
            doc_date = date_match.group(1)

        # Base date for relative temporal parsing (deterministic demo date if configured)
        base_date = doc_date or settings.get_effective_date()

        # Split text into candidate activity lines or sentences
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        candidate_lines = []

        for line in lines:
            # Strip leading list markers: 1., 1), -, *, etc.
            cleaned = re.sub(r"^(\d+[\.\)]|\-|\*)\s*", "", line).strip()
            
            # Filter out document metadata and section headers
            if self._is_header_or_metadata(line, cleaned):
                continue

            if len(cleaned.split()) >= 3:
                candidate_lines.append((line, cleaned))

        extracted_events = []

        for original_line, line in candidate_lines:
            # 1. Evidence text is the sentence itself
            evidence = line
            lower_line = line.lower()

            # 2. Check for quantity and unit
            qty = None
            unit = None

            # Check for partial pattern: e.g. "14 of 20 supports"
            part_m = re.search(r"(\d+(?:\.\d+)?)\s+of\s+\d+(?:\.\d+)?\s+([a-zA-Z]+)", line, re.IGNORECASE)
            if part_m:
                qty = float(part_m.group(1))
                unit = part_m.group(2).lower()
            else:
                matches = list(re.finditer(r"(?<![A-Za-z0-9\-])(\d+(?:\.\d+)?)\s*([a-zA-Z]+)?\b", line))
                for m in matches:
                    cand_qty = float(m.group(1))
                    raw_cand_unit = m.group(2)
                    cand_unit = raw_cand_unit.lower() if raw_cand_unit else None
                    if cand_unit and cand_unit in self.KNOWN_UNITS:
                        qty = cand_qty
                        unit = cand_unit
                        break
                    else:
                        # Check if subsequent word is a known unit (e.g. "8 pipe supports")
                        rest = line[m.end():]
                        next_m = re.match(r"^\s*([a-zA-Z]+)\b", rest)
                        if next_m and next_m.group(1).lower() in self.KNOWN_UNITS:
                            qty = cand_qty
                            unit = next_m.group(1).lower()
                            break
                        elif cand_unit and cand_unit not in self.QUANTITY_STOP_WORDS and qty is None:
                            qty = cand_qty
                            unit = cand_unit  # Preserved as text without crashing
                        elif not cand_unit and qty is None:
                            qty = cand_qty

            # 3. Status determination
            status = "IN_PROGRESS"
            for st, keywords in self.STATUS_KEYWORDS.items():
                if any(kw in lower_line for kw in keywords):
                    status = st
                    break

            # 4. Discipline determination
            discipline = None
            max_disc_matches = 0
            for disc, kw_list in self.DISCIPLINE_KEYWORDS.items():
                matches_count = sum(1 for kw in kw_list if kw in lower_line)
                if matches_count > max_disc_matches:
                    max_disc_matches = matches_count
                    discipline = disc

            # 5. Location extraction
            location = None
            for pat in self.LOCATION_PATTERNS:
                loc_m = re.search(pat, line, re.IGNORECASE)
                if loc_m:
                    location = loc_m.group(1).strip()
                    break

            # 6. Equipment ID extraction
            equipment_id = None
            for pat in self.EQUIPMENT_PATTERNS:
                eq_m = re.search(pat, line)
                if eq_m:
                    equipment_id = eq_m.group(1).strip()
                    break

            # 7. Progress percent estimation
            progress_pct = None
            pct_m = re.search(r"(\d+(?:\.\d+)?)\s*%", line)
            if pct_m:
                progress_pct = float(pct_m.group(1))
            elif status == "COMPLETED":
                progress_pct = 100.0

            # 8. Deterministic Date resolution
            from datetime import datetime, timedelta
            event_date = base_date
            if "yesterday" in lower_line:
                try:
                    dt = datetime.strptime(base_date[:10], "%Y-%m-%d")
                    event_date = (dt - timedelta(days=1)).strftime("%Y-%m-%d")
                except Exception:
                    event_date = base_date
            elif "today" in lower_line or not event_date:
                event_date = base_date

            # Filter out non-construction noise (like zero incident HSE statements if trivial)
            if "zero safety incidents" in lower_line and not discipline:
                continue

            # Activity description: cleaned representation of the line
            desc = line
            if len(desc) > 200:
                desc = desc[:200]

            extracted_events.append(FieldEventExtract(
                event_date=event_date,
                discipline=discipline,
                activity_description=desc,
                location=location,
                equipment_id=equipment_id,
                status=status,
                progress_percent=progress_pct,
                quantity=qty,
                unit=unit,
                source_reference=metadata.get("filename", "Field DPR"),
                evidence_text=evidence
            ))

        return extracted_events

class HostedLLMExtractor(LLMExtractor):
    """
    Hosted LLM Extractor (Gemini / OpenAI) with automatic fallback to deterministic extractor.
    Uses Gemini 2.5 Flash / Flash Latest for high-speed, grounded event extraction.
    """
    def __init__(self):
        self.fallback = RuleBasedFallbackExtractor()

    def extract_events(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[FieldEventExtract]:
        # If no external API key is provided, gracefully degrade to deterministic extractor
        api_key = settings.GEMINI_API_KEY or settings.OPENAI_API_KEY
        if not api_key:
            return self.fallback.extract_events(text, metadata)

        try:
            import httpx
            # Gemini Extraction Pipeline
            if settings.GEMINI_API_KEY:
                prompt = (
                    "You are InfraNexus AI extraction assistant for construction and pipeline engineering.\n"
                    "Extract progress events from the text into a JSON array.\n"

                    "Only extract facts explicitly stated in the text. Do not invent or guess WBS codes.\n"
                    f"Report Text:\n{text}\n\n"
                    "Return ONLY a valid JSON array of objects formatted exactly like this:\n"
                    "[\n"
                    "  {\n"
                    '    "event_date": "YYYY-MM-DD" or null,\n'
                    '    "discipline": "Piping" or "Civil" or "Mechanical" or "Electrical" or "Instrumentation" or "HSE" or null,\n'
                    '    "activity_description": "concise description of work performed",\n'
                    '    "location": "location tag (e.g. V-105, Pump House PH-1)" or null,\n'
                    '    "equipment_id": "equipment tag (e.g. V-105, P-101A)" or null,\n'
                    '    "status": "COMPLETED" or "IN_PROGRESS" or "NOT_STARTED",\n'
                    '    "progress_percent": float percentage 0-100 or null,\n'
                    '    "quantity": number or null,\n'
                    '    "unit": "unit string (e.g. spools, joints, m, cum)" or null,\n'
                    '    "evidence_text": "exact sentence snippet from report text justifying this event"\n'
                    "  }\n"
                    "]\n"
                    "Do NOT include markdown formatting, conversational text, or explanations. Only the raw JSON array."
                )
                
                models_to_try = ["gemini-2.5-flash", "gemini-flash-latest", "gemini-1.5-flash"]
                for model in models_to_try:
                    try:
                        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={settings.GEMINI_API_KEY}"
                        resp = httpx.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=20.0)
                        if resp.status_code == 200:
                            data = resp.json()
                            raw_out = data["candidates"][0]["content"]["parts"][0]["text"]
                            clean_json = re.sub(r"```json|```", "", raw_out).strip()
                            json_match = re.search(r"\[.*\]", clean_json, re.DOTALL)
                            if json_match:
                                items = json.loads(json_match.group(0))
                                if isinstance(items, list) and len(items) > 0:
                                    extracted = []
                                    for item in items:
                                        status_val = str(item.get("status", "IN_PROGRESS")).upper()
                                        if status_val not in ["COMPLETED", "IN_PROGRESS", "NOT_STARTED"]:
                                            status_val = "IN_PROGRESS"
                                        prog_pct = item.get("progress_percent")
                                        if prog_pct is None and status_val == "COMPLETED":
                                            prog_pct = 100.0
                                        elif prog_pct is not None:
                                            try:
                                                prog_pct = float(prog_pct)
                                            except (ValueError, TypeError):
                                                prog_pct = 0.0
                                        qty = item.get("quantity")
                                        if qty is not None:
                                            try:
                                                qty = float(qty)
                                            except (ValueError, TypeError):
                                                qty = None

                                        extracted.append(FieldEventExtract(
                                            event_date=item.get("event_date") or (metadata.get("date") if metadata else None),
                                            discipline=item.get("discipline"),
                                            activity_description=item.get("activity_description") or text[:100],
                                            location=item.get("location"),
                                            equipment_id=item.get("equipment_id"),
                                            status=status_val,
                                            progress_percent=prog_pct,
                                            quantity=qty,
                                            unit=item.get("unit"),
                                            source_reference=metadata.get("filename", "Field DPR") if metadata else "Field DPR",
                                            evidence_text=item.get("evidence_text") or text[:150]
                                        ))
                                    if extracted:
                                        print(f"INFO: InfraNexus AI successfully extracted {len(extracted)} events using live Gemini ({model})")
                                        return extracted

                    except Exception as me:
                        print(f"INFO: Gemini model {model} attempt: {me}")
                        continue
        except Exception as e:
            print(f"WARNING: Hosted LLM extraction error: {e}. Falling back to deterministic NLP.")

        return self.fallback.extract_events(text, metadata)

def get_extractor() -> LLMExtractor:
    if settings.AI_PROVIDER != "fallback" and (settings.GEMINI_API_KEY or settings.OPENAI_API_KEY):
        return HostedLLMExtractor()
    return RuleBasedFallbackExtractor()

