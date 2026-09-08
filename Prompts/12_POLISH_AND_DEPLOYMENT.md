# PROMPT 12 — FINAL POLISH + DEPLOYMENT

Only after all previous phases pass.

## Polish
Fix:
- broken states
- inconsistent terminology
- unreadable tables
- long labels
- bad empty states
- loading flicker
- stale cached data
- duplicated actions
- console errors
- backend exceptions

## Terminology
Use:
Field Event
L5/L6 Activity
Candidate Match
Confidence
Planner Review
Approved Update
Unmatched
Audit Trail

## Health
Expose an internal system-health panel or endpoint for demo troubleshooting:
- backend
- database
- AI provider
- embedding provider
- demo mode

## Deployment
Prefer simple:
- frontend: Vercel or local
- backend: Render/Railway or local
- PostgreSQL: managed or local

Provide:
- .env.example
- deployment notes
- CORS config
- database migration/seed instructions

Do NOT require production-grade enterprise infrastructure for the MVP.

## Security basics
- no secrets in Git
- validate uploaded files
- size/type limits
- sanitize file names
- avoid arbitrary path writes
- parameterized DB queries through ORM
- no raw model output injected as HTML
- log safely without sensitive source text where possible

## Final audit
Search codebase for:
TODO
FIXME
mock
dummy
fake
hardcoded

Remove or clearly isolate anything that would mislead a judge into thinking a feature is real.

## Final report
Create docs/final-mvp-status.md:
- built now
- optional/demo-only
- future
- known limitations
- exact run commands
- test status
