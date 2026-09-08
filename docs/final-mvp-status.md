# PRAGATI AI — Final MVP Status Report

**Team:** InfraNexus  
**Project:** PRAGATI AI  
**Problem Statement:** SIH26122 (Oil India Limited)  

---

## 1. What is Built & Fully Functional Now

1. **Schedule Ingestion Layer:**
   - Flexible column alias resolver (`Activity ID`, `WBS`, `Description`, `Discipline`, `Location`, `Equipment`, `Planned Start`, `Planned Finish`, `Planned Progress`).
   - Supports both `.csv` and native zipped XML `.xlsx` spreadsheets.
2. **Field Document Ingestion:**
   - Handles raw `.txt`, `.csv`, and PDF files (with text extraction using `pypdfium2` and `pdfminer.six`).
3. **Structured Event Extraction:**
   - Strict Pydantic extraction schema (`FieldEventExtract`).
   - Provider abstraction: Supports hosted Gemini/OpenAI models when configured, and features an offline-first **Deterministic NLP & Rule-Based Fallback Extractor**.
   - Preserves grounded sentence evidence.
4. **Multi-Signal Matching Engine:**
   - Semantic similarity using TF-IDF and Cosine Vector Space (`scikit-learn`).
   - Discipline compatibility scoring (1.0 exact, 0.4 compatible, 0.0 conflict).
   - Entity & equipment identifier matching (1.0 exact, 0.0 mismatch).
   - Location tag matching (1.0 exact, 0.7 partial, 0.0 mismatch).
   - Temporal schedule window soft evaluation.
   - Contradiction penalty overrides (prevents matches on conflicting locations or work types).
   - Margin-based confidence tiering (`HIGH`, `MEDIUM`, `LOW`, `UNMATCHED`).
5. **Human-in-the-Loop Governance:**
   - AI proposes; Planner decides.
   - One-click **Approve**, modal-assisted **Edit & Approve**, and **Reject**.
   - Atomic database transactions with idempotency protection.
6. **Immutable Audit Trail:**
   - Records event ID, source document, AI suggested candidate and score, planner action, before-state vs after-state, actor, and timestamp.
7. **Executive Dashboard & Workstation UI:**
   - Real-time S-curve graph comparing planned baseline vs actual progress.
   - Split-screen inspection workstation showing highlighted evidence alongside top candidates and score meters.
   - Schedule activity master table.
   - 100% data-backed metrics (zero mock numbers).
8. **Automated Verification:**
   - 15 automated pytest tests passing.
   - Evaluation runner producing ground-truth metrics.

---

## 2. Deterministic Demo & Offline Fallback

The entire pipeline runs without external API keys or an active internet connection. The local TF-IDF model and deterministic entity extractor ensure that:
- The **Hero Case** ranks `PIP-L6-0427` #1 with HIGH confidence.
- The **Ambiguous Case** flags a close tie and routes to MEDIUM confidence.
- The **Unmatched Case** safely scores 0.0 without mutating the schedule.
- The **Reset Demo** button (`POST /api/demo/reset`) restores the database to initial baseline in milliseconds.

---

## 3. Known Prototype Limitations & Future Enhancements

- **Scanned Optical Character Recognition (OCR):** Scanned handwritten or image-only PDFs require Tesseract or cloud Vision APIs; the MVP focuses on standard text PDFs and digital text DPRs.
- **Enterprise ERP/Primavera Live Synchronization:** The prototype uses Excel/CSV schedule imports; live bidirectional Primavera P6 API syncing is scheduled for post-hackathon enterprise deployment.
- **Audio/Voice Ingestion:** Speech-to-text integration for site voice notes is designed as a future modular ingestion plugin.

---

## 4. Run Commands

### Start Prototype:
```powershell
python run.py
```
*Access UI at `http://127.0.0.1:8000`*

### Run Test Suite:
```powershell
python -m pytest tests/ -v -p no:cacheprovider
```

### Run Benchmark Evaluation:
```powershell
python scripts/evaluate.py
```

### Reset Demo Environment:
```powershell
python scripts/seed_demo.py
```
