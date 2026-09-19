# InfraNexus AI — Ground-Truth Evaluation Report

**Date:** 2026-09-19 22:54:55
**Problem Statement:** SIH26122 (Oil India Limited)
**Team:** Infranexus
**Mode:** Deterministic Offline Fallback (Local Scikit TF-IDF & Deterministic NLP Rules)

## 1. Benchmark Targets vs Measured Results

| Evaluation Dimension | Benchmark Target | Measured Result | Status |
|---|---|---|---|
| Clear Match Top-1 Accuracy | > 75.0% | **100.0%** | ✅ PASSED |
| Top-3 Candidate Recall | > 90.0% | **100.0%** | ✅ PASSED |
| Ambiguity Routing Accuracy | > 80.0% | **100.0%** | ✅ PASSED |
| No-Match Detection Accuracy | > 80.0% | **100.0%** | ✅ PASSED |
| Pipeline Latency (per event) | < 250 ms | **7.85 ms** | ✅ PASSED |

## 2. Controlled Scenario Verification Matrix

| Event ID | Scenario Type | Expected Target | Predicted Top-1 | Confidence Tier | Match Score | Verification Status |
|---|---|---|---|---|---|---|
| EVT-HERO-001 | HERO_SUCCESS | `PIP-L6-0427` | `PIP-L6-0427` | HIGH | 0.745 | ✅ PASSED |
| EVT-AMBIG-002 | AMBIGUOUS_CHOICE | `PIP-L6-0501|PIP-L6-0502` | `PIP-L6-0502` | MEDIUM | 0.664 | ✅ PASSED |
| EVT-UNMATCH-003 | NO_MATCH | `UNMATCHED` | `UNMATCHED` | UNMATCHED | 0.000 | ✅ PASSED |
| EVT-SYNONYM-004 | SYNONYM_PHRASING | `PIP-L6-0427` | `PIP-L6-0427` | HIGH | 0.753 | ✅ PASSED |
| EVT-NOMATCH-005 | NO_MATCH | `UNMATCHED` | `UNMATCHED` | UNMATCHED | 0.323 | ✅ PASSED |
| EVT-HERO-006 | HERO_SUCCESS | `PIP-L6-0427` | `PIP-L6-0427` | HIGH | 0.789 | ✅ PASSED |

## 3. Evaluation Methodology & Governance Principles
1. **Deterministic Demo Baseline:** Multi-signal matching (semantic 0.50, discipline 0.15, entity 0.15, location 0.10, temporal 0.10).
2. **Separation of Ambiguity from Failure:** Ambiguous real-world reports with close competitive candidates are routed to human review (MEDIUM) rather than forcing an inaccurate Top-1 mutation.
3. **Unmatched Grounding:** Field logs describing activities not present in the master schedule are safely preserved as UNMATCHED without corrupting the schedule.
