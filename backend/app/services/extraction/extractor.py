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
        
        # Try to parse date from document header if present
        date_match = re.search(r"Date:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})", text, re.IGNORECASE)
        if date_match:
            doc_date = date_match.group(1)

        # Split text into candidate activity lines or sentences
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        candidate_lines = []

        for line in lines:
            # Match lines starting with numbers/bullets or action descriptions
            cleaned = re.sub(r"^\d+[\.\)]\s*", "", line)
            # Filter out headers and metadata lines
            if any(cleaned.lower().startswith(h) for h in ["oil india", "project:", "report ref:", "site engineer:", "area:", "daily progress report"]):
                continue
            if len(cleaned.split()) >= 3:
                candidate_lines.append((line, cleaned))

        extracted_events = []

        for original_line, line in candidate_lines:
            # 1. Evidence text is the sentence itself
            evidence = line

            # 2. Check for quantity and unit
            # Example: "14 spools installed", "4 joints", "45 cum", "100 m"
            qty = None
            unit = None
            matches = list(re.finditer(r"(?<![A-Za-z0-9\-])(\d+(?:\.\d+)?)\s+([a-zA-Z]+)\b", line))
            stop_words = {"hours", "days", "shifts", "am", "pm", "today", "yesterday", "completed", "installed", "erected", "started", "done", "near", "at", "in", "the", "with"}
            known_units = {"spools", "spool", "joints", "joint", "cum", "m", "units", "unit", "meters", "meter", "panels", "panel", "loops", "loop", "valves", "valve", "pieces", "piece", "tonnes", "tonne", "checkpoints"}
            
            for m in matches:
                cand_qty = float(m.group(1))
                cand_unit = m.group(2).lower()
                if cand_unit in known_units:
                    qty = cand_qty
                    unit = cand_unit
                    break
                elif cand_unit not in stop_words and qty is None:
                    qty = cand_qty
                    unit = cand_unit
                    unit = candidate_unit

            # 3. Status determination
            status = "IN_PROGRESS"
            lower_line = line.lower()
            for st, keywords in self.STATUS_KEYWORDS.items():
                if any(kw in lower_line for kw in keywords):
                    status = st
                    break

            # 4. Discipline determination
            discipline = None
            max_disc_matches = 0
            for disc, kw_list in self.DISCIPLINE_KEYWORDS.items():
                matches = sum(1 for kw in kw_list if kw in lower_line)
                if matches > max_disc_matches:
                    max_disc_matches = matches
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

            # 8. Date resolution
            event_date = doc_date
            if "today" in lower_line and doc_date:
                event_date = doc_date

            # Filter out non-construction noise (like zero incident HSE statements if trivial)
            if "zero safety incidents" in lower_line and not discipline:
                continue

            # Activity description: cleaned representation of the line
            desc = line
            # Truncate if too long
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
                    "You are PRAGATI AI extraction assistant for construction and pipeline engineering.\n"
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
                                        print(f"INFO: PRAGATI AI successfully extracted {len(extracted)} events using live Gemini ({model})")
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

