# ONE-SHOT MASTER PROMPT FOR ANTIGRAVITY

You are the senior full-stack + AI engineer responsible for implementing PRAGATI AI, a working MVP for Smart India Hackathon 2026 PS SIH26122.

Team: InfraNexus
Project: PRAGATI AI
Product positioning: AI-Powered Planning-to-Execution Intelligence Layer.

The complete requirements are in the markdown files in this workspace. Read ALL of them before coding:
00_README_FIRST.md
01_MASTER_CONTEXT.md
02_ARCHITECTURE_AND_REPO.md
03_DATASET_GENERATION.md
04_BACKEND_FOUNDATION.md
05_EXTRACTION_PIPELINE.md
06_MATCHING_ENGINE.md
07_APPROVAL_AND_AUDIT.md
08_FRONTEND_DASHBOARD.md
09_END_TO_END_INTEGRATION.md
10_TESTING_AND_VALIDATION.md
11_DEMO_SEED_AND_FALLBACK.md
12_POLISH_AND_DEPLOYMENT.md

Then implement the project incrementally in the repository.

CRITICAL:
- Do not only generate files. Run them.
- Do not stop at scaffolding.
- After each major phase, start the application and run tests.
- Fix errors before continuing.
- Use real backend/database state.
- Do not fake numbers in dashboard cards.
- AI may suggest; planner decides.
- Never silently mutate the schedule.
- Keep a deterministic offline fallback so the hero demo works without external APIs.
- Use synthetic data only.
- Do not claim Primavera integration exists.
- Do not include production-only complexity unless it directly supports the MVP.

PRIORITY ORDER:
1. matching correctness
2. extraction correctness
3. human approval/governance
4. persistence/audit
5. end-to-end reliability
6. dashboard polish

DEMO REQUIREMENT:
A judge uploads:
"Spool erection near V-105 completed today. 14 spools installed."

The app should extract:
activity type = erection
object = spool/line
location = V-105
quantity = 14
unit = spools
status = completed

It should rank:
PIP-L6-0427 — Erect Line 24-inch near V-105

It should show component scores and confidence.
The planner approves.
Actual progress changes.
The audit trail records the entire chain.

Then demonstrate:
- one ambiguous MEDIUM case
- one no-match LOW/UNMATCHED case

DO NOT hardcode PIP-L6-0427 as the result.
The result must emerge from the matching engine.

When done:
1. run tests
2. run the end-to-end demo
3. write docs/final-mvp-status.md
4. write docs/acceptance-report.md
5. document exact commands
6. list known limitations

Work until the MVP is actually usable, not merely coded.
