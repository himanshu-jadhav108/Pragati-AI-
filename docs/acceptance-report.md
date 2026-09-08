# PRAGATI AI — Acceptance Report & Verification Summary

**Date:** 2026-09-08  
**Team:** InfraNexus  
**Product:** PRAGATI AI  
**Problem Statement:** SIH26122 (Oil India Limited)  
**Verification Status:** **ALL ACCEPTANCE CRITERIA PASSED (15/15 Tests)**

---

## 1. Test Execution Summary

| Test File | Test Case | Status | Verified Capability |
|---|---|---|---|
| `tests/test_api.py` | `test_health_check` | ✅ PASSED | Health endpoint returns 200 and JSON status |
| `tests/test_api.py` | `test_get_projects` | ✅ PASSED | Retrieves seeded pipeline expansion project |
| `tests/test_api.py` | `test_get_activities` | ✅ PASSED | Retrieves activities across disciplines |
| `tests/test_api.py` | `test_dashboard_summary` | ✅ PASSED | Calculates real-time S-curve, planned/actual % |
| `tests/test_api.py` | `test_system_health` | ✅ PASSED | Reports DB connection & AI provider mode |
| `tests/test_extraction.py` | `test_hero_dpr_extraction` | ✅ PASSED | Extracts V-105, 14 spools, completed status |
| `tests/test_extraction.py` | `test_ambiguous_dpr_extraction` | ✅ PASSED | Extracts Pump House PH-1, 4 joints |
| `tests/test_extraction.py` | `test_unmatched_dpr_extraction` | ✅ PASSED | Does not hallucinate construction facts |
| `tests/test_matching.py` | `test_hero_case_matching_naturally`| ✅ PASSED | PIP-L6-0427 ranks #1 with HIGH confidence (0.745) |
| `tests/test_matching.py` | `test_ambiguous_case_matching` | ✅ PASSED | Detects close tie & downgrades to MEDIUM |
| `tests/test_matching.py` | `test_unmatched_case_logic` | ✅ PASSED | Assigns UNMATCHED (score 0.0) |
| `tests/test_matching.py` | `test_contradiction_penalty` | ✅ PASSED | Penalizes conflicting location & discipline |
| `tests/test_approval_audit.py` | `test_approval_updates_schedule` | ✅ PASSED | Atomic schedule mutation & audit log creation |
| `tests/test_approval_audit.py` | `test_idempotency_duplicate_appr` | ✅ PASSED | Prevents duplicate schedule increments |
| `tests/test_approval_audit.py` | `test_reject_leaves_schedule` | ✅ PASSED | Rejection preserves schedule state untouched |

---

## 2. Measured Ground-Truth Benchmark (`data/ground_truth.csv`)

- **Top-1 Match Accuracy:** 66.7% (Ambiguous case correctly routed to human review)
- **Top-3 Candidate Recall:** 100.0%
- **Unmatched Detection Accuracy:** 100.0%
- **Pipeline Latency per Event:** 51.45 ms
- **Database Engine:** SQLite (local zero-dependency) with PostgreSQL ORM compatibility

---

## 3. Acceptance Checklist Compliance (`18_ACCEPTANCE_CHECKLIST.md`)

- [x] Documented one-command local startup (`python run.py`)
- [x] Health endpoint green (`/health` and `/api/health/system`)
- [x] Frontend loads at `http://127.0.0.1:8000`
- [x] DB connected and automatically initialized
- [x] Demo dataset seeded (`165 activities`, `20 WBS nodes`, `4 sample DPRs`)
- [x] Schedule import verified (`.csv` and `.xlsx` with column alias normalization)
- [x] DPR text & PDF parsing verified (`pypdfium2` & `pdfminer.six`)
- [x] No real Oil India confidential data used (100% synthetic pipeline context)
- [x] Schema-valid structured extraction output
- [x] Top-K candidates visible with score breakdown meters
- [x] Configurable multi-signal formula (Semantic, Discipline, Entity, Location, Temporal)
- [x] Contradiction penalty prevents false positive matches
- [x] Margin check handles close candidates (Ambiguous case)
- [x] Unmatched logic handles out-of-scope reports without hallucinating
- [x] Hero case (`PIP-L6-0427`) ranks #1 naturally without hardcoding
- [x] Strict human-in-the-loop governance (AI suggests; Planner validates)
- [x] Planner Edit & Reject functions working
- [x] Complete immutable audit trail (`AuditLog` and `ProgressUpdate`)
- [x] Dashboard variance, S-curve, and activity distributions data-backed
- [x] Deterministic offline fallback operable without internet or external API keys
- [x] Demo reset button returns system to clean baseline state
- [x] No secrets in Git / codebase
