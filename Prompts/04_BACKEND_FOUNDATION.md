# PROMPT 04 — BACKEND FOUNDATION

Read the master context and architecture files.

Implement the real FastAPI backend foundation.

## Database model
At minimum:
Project
WBSNode
Activity
Document
FieldEvent
Match
ProgressUpdate
AuditLog
DelayEvent

Useful fields include:
- UUID/int primary keys
- project_id
- parent_wbs_id
- activity_id
- source_document_id
- source_text/reference
- event_date
- discipline
- activity_description
- location
- equipment_id
- status
- progress_percent
- quantity
- unit
- extraction_confidence
- match_score
- confidence_tier
- decision
- decided_by
- decided_at
- before_value
- after_value
- created_at
- updated_at

## Import
Implement Excel/CSV schedule import with validation.
Support reasonable column aliases:
Activity ID / Activity_ID / activity_id
Description / Activity Description
Discipline
WBS
Location
Equipment
Planned Start
Planned Finish
Planned Progress

Normalize dates and percentages.

Reject malformed rows with useful errors, while allowing valid rows to import.

## Document ingestion
Support:
- .txt
- text-based .pdf

Store original metadata and extracted text.

Use PyMuPDF for normal PDFs.
Do not make OCR a blocker.

## API
Implement the endpoints from the architecture prompt.
Use real DB operations.

## Seed
Create:
scripts/seed_demo.py

Seed:
- one project
- hierarchy
- activities
- sample DPRs
- some already-approved progress
- one delayed activity
- one unmatched event

## Quality gate
Run backend tests for:
- health
- schedule import
- document upload
- seed
- basic queries

Return structured JSON.
Do not return arbitrary strings where schemas are expected.
