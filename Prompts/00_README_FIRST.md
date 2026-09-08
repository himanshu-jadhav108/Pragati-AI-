# PRAGATI AI — Antigravity MVP Prompt Pack

Team Name: InfraNexus
Project Name: PRAGATI AI
Problem Statement: SIH26122
Organization: Oil India Limited

## Goal
Build a WORKING, DEMO-READY MVP that proves the core planning-to-execution bridge:

DPR/text/Excel
→ structured progress event extraction
→ L5/L6 candidate retrieval
→ semantic + contextual scoring
→ confidence tier
→ planner approval
→ schedule-linked actual update
→ audit trail
→ live planned-vs-actual dashboard

This MVP is NOT a generic project-management dashboard.

## Critical rule
The system must never silently edit the schedule. AI proposes. A human planner approves/edits/rejects. Every committed change is auditable.

## Use these prompts in order
1. 01_MASTER_CONTEXT.md
2. 02_ARCHITECTURE_AND_REPO.md
3. 03_DATASET_GENERATION.md
4. 04_BACKEND_FOUNDATION.md
5. 05_EXTRACTION_PIPELINE.md
6. 06_MATCHING_ENGINE.md
7. 07_APPROVAL_AND_AUDIT.md
8. 08_FRONTEND_DASHBOARD.md
9. 09_END_TO_END_INTEGRATION.md
10. 10_TESTING_AND_VALIDATION.md
11. 11_DEMO_SEED_AND_FALLBACK.md
12. 12_POLISH_AND_DEPLOYMENT.md

Use 13_DEBUG prompts if anything fails.

## Definition of Done
A fresh clone can:
- start backend and frontend with documented commands
- load seeded synthetic schedule + DPR examples
- upload/import an Excel schedule
- upload a text/PDF DPR
- extract structured progress events
- retrieve and score L5/L6 candidates
- show HIGH/MEDIUM/LOW confidence
- show source evidence and rationale
- let a planner approve/edit/reject
- update actual progress only after approval
- write an audit record
- reflect the update on the dashboard
- show unmatched/ambiguous cases without force-matching
- run automated tests
- work in demo fallback mode without live LLM connectivity

## Product principles
1. Core innovation = event-to-schedule matching + confidence + governance.
2. LLM is a component, not the product.
3. Prefer deterministic code around AI outputs.
4. No fake metrics.
5. No confidential Oil India data.
6. Use synthetic but realistic construction/pipeline data.
7. Keep MVP narrow and reliable.

## Preferred stack
Frontend: Next.js + TypeScript + Tailwind + shadcn/ui + Recharts
Backend: Python + FastAPI + Pydantic + SQLAlchemy
DB: PostgreSQL + pgvector where available; provide a local fallback if vector extension/setup is unavailable
Docs: PyMuPDF + pandas + openpyxl
AI: provider abstraction for structured LLM extraction + embeddings
Infra: Docker/compose optional; local-first developer experience

## Demo hero
Field report:
"Spool erection near V-105 completed today. 14 spools installed."

Expected schedule candidate:
PIP-L6-0427 — "Erect Line 24-inch near V-105"

Show:
- extracted event
- top candidates
- semantic similarity
- contextual signals
- final score
- confidence tier
- planner approval
- actual progress update
- audit trail

Also demonstrate one LOW-confidence unmatched/ambiguous event.

## Important engineering behavior
- LLM extraction failures must degrade gracefully.
- Embedding provider failures must degrade to a deterministic local lexical/feature scorer.
- PDF text extraction must work without OCR for normal text PDFs.
- Scanned OCR is optional, not on the critical demo path.
- Live voice is NOT MVP.
- Primavera/MS Project live integration is NOT MVP.
