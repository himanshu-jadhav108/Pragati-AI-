# PROMPT 07 — PLANNER APPROVAL + AUDIT GOVERNANCE

Implement the human-in-the-loop workflow.

## Rule
The AI cannot commit schedule-changing updates.

## Review screen must show
- source DPR/document
- extracted event
- top candidate
- alternative candidates
- all component scores
- final confidence
- rationale
- current activity state
- proposed update
- evidence

## Actions
Approve:
- apply proposed update
- create ProgressUpdate
- create AuditLog

Edit:
- planner selects a different activity and/or changes progress/status/date
- apply edited result
- create audit record showing AI suggestion vs human final decision

Reject:
- no schedule update
- audit rejection

Unmatched:
- allow planner to resolve manually
- or mark as ignored/unmatched
- never force a match

## Audit record
Every committed decision stores:
- event id
- source document id
- AI top candidate
- AI score
- AI confidence
- planner decision
- final activity id
- previous schedule state
- resulting state
- actor
- timestamp
- action

## Idempotency
Approving the same match twice must NOT duplicate progress updates.
Use a state transition or idempotency key.

## Transactional behavior
Approval and audit should be atomic:
either both commit or neither commits.

## Business rules
- completed event should not reduce actual progress
- actual progress should be bounded 0..100
- actual finish should be set only when status/completion evidence justifies it
- do not overwrite planned dates with actual dates
- preserve original source evidence

## UI
Make approval feel like a planner workstation, not a chatbot.

Show:
HIGH — suggested update
MEDIUM — review required
LOW/UNMATCHED — manual attention

Add filters by:
confidence
discipline
status
project
date
