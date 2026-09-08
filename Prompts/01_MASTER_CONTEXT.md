# MASTER CONTEXT — PRAGATI AI MVP

## Identity
Team: InfraNexus
Product: PRAGATI AI
Subtitle: AI-Powered Planning-to-Execution Intelligence Layer
SIH PS: SIH26122
Organization: Oil India Limited

## Problem
Infrastructure project schedules are maintained at detailed L5/L6 activity levels, while actual execution information arrives as fragmented daily progress reports, spreadsheets, site diaries, and verbal/text updates. Field terminology and schedule terminology do not always match. Planners therefore manually reconcile field evidence against the schedule, creating delay, inconsistency and weak traceability.

## Solution
PRAGATI AI is an AI-assisted translation/governance layer between field execution data and the approved schedule.

Pipeline:
UNSTRUCTURED FIELD DATA
→ AI EXTRACTION
→ STRUCTURED PROGRESS EVENT
→ L5/L6 ACTIVITY CANDIDATE RETRIEVAL
→ SEMANTIC + CONTEXTUAL MATCHING
→ CONFIDENCE SCORE
→ PLANNER VALIDATION
→ APPROVED PROGRESS UPDATE
→ DASHBOARD / ANALYTICS
→ AUDIT TRAIL

## Users
Site Engineer:
- submits DPR/text or document
- does not need to know schedule IDs

Planner:
- reviews candidate activities
- approves/edits/rejects
- owns schedule-changing decisions

Project Manager:
- sees current planned vs actual progress
- sees pending validation and unmatched events

## MVP scope
Must support:
1. Excel schedule import
2. DPR text/PDF upload
3. structured event extraction
4. L5/L6 matching
5. confidence tiering
6. planner approval/edit/reject
7. actual progress update
8. dashboard
9. audit trail
10. synthetic seed data
11. end-to-end tests
12. offline/demo fallback

Optional only after core is stable:
- OCR for scanned documents
- simple uploaded voice transcript

Explicitly out:
- live Primavera integration
- enterprise SSO/RBAC
- mobile app
- predictive schedule risk
- multilingual production support
- live voice agent

## Core matching logic
Start with:
candidate retrieval → semantic similarity → structured feature matching → weighted score.

Baseline score:
0.50 semantic similarity
+ 0.15 discipline
+ 0.15 entity/equipment
+ 0.10 location/WBS
+ 0.10 temporal/schedule context

Treat weights as tunable configuration, not immutable truth.

## Confidence routing
HIGH:
- clear winner
- strong score
- enough corroborating signals
- planner gets a one-click approval suggestion

MEDIUM:
- plausible candidates / moderate certainty
- planner must review and choose

LOW:
- weak evidence or ambiguity
- no automatic schedule action

NO MATCH:
- explicitly mark unmatched
- never force a schedule activity

## Governance
No schedule mutation before planner approval.
Store:
- source document/event
- extracted fields
- candidate matches
- scoring signals
- confidence
- planner action
- before state
- after state
- timestamp
- user

## Honest prototype posture
Do not claim real Oil India data, live Primavera connectivity, achieved accuracy or production readiness.
Use synthetic data and label benchmark numbers as measured only after tests have run.

## Expected architecture
Next.js UI
→ FastAPI
→ document parser/importer
→ extraction service
→ matching service
→ validation service
→ PostgreSQL/pgvector
→ dashboard/audit.

Keep providers abstract so LLM/embedding vendors can be swapped.

## Quality bar
The prototype must be usable by a judge without developer intervention:
- seeded project exists
- sample DPR is one click away
- matching result is understandable
- approval visibly changes actuals
- audit record is visible
- refresh does not lose committed data
- error states are friendly
- demo still works if external AI is unavailable
