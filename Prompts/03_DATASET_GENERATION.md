# PROMPT 03 — SYNTHETIC DATASET

Build the synthetic dataset that makes PRAGATI AI testable.

## Goal
Create realistic pipeline/infrastructure construction schedule data, deliberately containing terminology mismatch.

## Required entities
- projects
- WBS levels L1-L6
- activities
- disciplines
- locations
- equipment
- planned start/finish
- planned progress
- DPR documents
- field events
- ground-truth matches
- delay examples

## Target size
Start smaller for development:
- 150–250 activities
- 30–50 DPRs
- 150–300 field events

Then provide a generator that can scale toward:
- 200–500 activities
- 50–100 DPRs
- 300–1,000 events

## Disciplines
At minimum:
Piping
Civil
Mechanical
Electrical
Instrumentation
HSE

## Terminology variation
For the same activity, vary field wording:
- spool erected
- spool erection completed
- line spool installed
- piping spool installation done
- mounted the spool
- fit-up/erection completed

Also create:
- equipment nicknames
- abbreviated locations
- alternate date formats
- quantities and units
- partial progress
- completion statements
- ambiguous events
- deliberate no-match events

## Required hero case
Activity:
PIP-L6-0427
Description:
Erect Line 24-inch near V-105
Discipline:
Piping
Location:
V-105

DPR:
"Spool erection near V-105 completed today. 14 spools installed."

Ground truth:
PIP-L6-0427

## Required hard cases
1. Exact semantic match with different wording
2. Two similar activities differentiated by location
3. Two similar activities differentiated by equipment
4. Missing location
5. Missing discipline
6. Partial progress
7. Ambiguous candidate set
8. No matching activity
9. Out-of-schedule activity
10. Duplicate/near-duplicate DPR phrasing

## Files to generate
data/
  schedule.csv
  wbs.csv
  activities.csv
  dprs/
  field_events.csv
  ground_truth.csv
  demo/
  README.md

Create scripts/generate_dataset.py with deterministic seed.

Validate referential integrity and ground truth.
