# PROMPT 02 — ARCHITECTURE + REPOSITORY

You are now the lead software architect for PRAGATI AI.

Read 01_MASTER_CONTEXT.md first.

Your job is to establish a clean, maintainable repo that can be completed by a student team using AI coding assistance.

## Deliver
Create:
- frontend/
- backend/
- data/
- scripts/
- tests/
- docs/
- .env.example
- README.md
- docker-compose.yml where practical

Use a monorepo unless the existing workspace already has a better structure.

## Backend modules
Prefer:
backend/app/
  main.py
  core/
  db/
  models/
  schemas/
  api/
  services/
    ingestion/
    extraction/
    matching/
    confidence/
    validation/
    audit/
    analytics/
  utils/

## Frontend modules
Prefer:
frontend/app/
frontend/components/
frontend/lib/
frontend/types/

Screens:
- dashboard
- ingestion
- review queue
- event detail
- activity detail
- audit trail
- settings/system health

## API contract
Create documented endpoints for:
GET /health
GET /api/projects
GET /api/activities
POST /api/schedules/import
POST /api/documents
POST /api/extractions/{document_id}/run
GET /api/events
GET /api/matches/{event_id}
POST /api/matches/{match_id}/approve
POST /api/matches/{match_id}/reject
POST /api/matches/{match_id}/edit
GET /api/dashboard/summary
GET /api/audit
POST /api/demo/reset

Do not build unnecessary CRUD endpoints.

## Architecture requirements
- Pydantic schemas at boundaries
- SQLAlchemy models
- service layer for business logic
- configuration from environment
- structured logging
- predictable error responses
- no hardcoded secrets
- provider abstraction for LLM/embeddings
- deterministic fallback implementations
- migrations if practical
- seed script

## Important
Do not fake backend responses in the final UI.
Every visible MVP workflow should call the actual API or explicitly use a documented demo fallback mode.

Before moving on, run the app and prove:
- frontend starts
- backend starts
- health endpoint works
- DB connection works
- seed script can run

Document exact commands.
