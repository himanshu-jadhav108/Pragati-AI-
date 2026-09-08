# PROMPT 11 — DEMO MODE + OFFLINE FALLBACK

Build a robust demo mode.

## Hero scenario
Initial state:
- project has planned progress ahead of actual progress
- PIP-L6-0427 is behind/not yet updated

Input:
"Spool erection near V-105 completed today. 14 spools installed."

Expected:
event extracted
PIP-L6-0427 ranked #1
high confidence
planner approval
actual progress/finish update
dashboard variance changes
audit trail visible

## Ambiguous scenario
Input should map plausibly to two schedule activities.
System must show MEDIUM confidence and require planner choice.

## Unmatched scenario
Input describes an activity absent from the schedule.
System must say UNMATCHED and perform no schedule update.

## Offline fallback
The demo must work with:
- no LLM key
- no embedding key
- no internet

Fallback architecture:
- seeded DPR text
- deterministic extractor
- local lexical/TF-IDF semantic scorer
- seeded dataset
- local DB

Make a clearly visible status:
"AI Provider: Live" or "Demo/Fallback Mode"

Do not pretend fallback output came from a live model.

## Demo reset
Provide a button/API that returns the app to clean demo state.

## Reliability
The first demo path should avoid scanned OCR and voice.
Do not make those prerequisites.

## Optional screen recording helper
Create docs/demo-script.md containing the 3–5 minute sequence and exact clicks.
