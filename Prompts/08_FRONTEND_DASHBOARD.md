# PROMPT 08 — FRONTEND

Build a polished but functional enterprise UI.

Read all context first.

## Visual direction
Light theme.
White/light gray background.
Dark navy/slate text.
Blue/teal accents.
Thin connectors.
Rounded cards.
Minimal gradients.
No cyberpunk.
No generic AI robot imagery.

## Pages

### Dashboard
Show:
- project selector
- planned progress
- actual progress
- variance
- pending reviews
- high/medium/low matches
- unmatched count
- recent approved updates
- planned-vs-actual chart
- activity status table

### Ingestion
- drag/drop or file picker
- accepted file types
- upload status
- parse result
- "Run extraction"

### Review Queue
Table/cards:
source
event
candidate
score
confidence
discipline
date
action

### Review Detail
Two-column layout:
left: source evidence
right: event + candidates + score breakdown + proposed update

Actions:
Approve
Edit & approve
Reject
Mark unmatched

### Activity detail
Schedule fields:
activity ID
WBS
description
discipline
location
equipment
planned dates
planned progress
actual progress
actual start
actual finish
source evidence links
audit history

### Audit
Timeline:
source → extraction → matching → planner decision → update

## UX requirements
- visible loading states
- empty states
- error states
- toast confirmations
- no fake progress bars
- keyboard-accessible controls
- responsive enough for laptop demo
- no tiny unreadable text

## Real data only
Wire pages to backend APIs.
Do not put static numbers in components except documented empty/demo placeholders.

## Demo helper
Add a small "Load Demo Scenario" button only if necessary.
It must call an API that seeds/resets data, not merely replace UI state.

## Quality gate
A judge should understand the workflow without reading documentation.
