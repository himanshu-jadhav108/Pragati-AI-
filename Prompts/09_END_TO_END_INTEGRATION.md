# PROMPT 09 — END-TO-END INTEGRATION

Now connect the complete workflow.

## Required journey
1. Seed/load demo project
2. Show schedule and stale actuals
3. Upload hero DPR
4. Extract event(s)
5. Retrieve candidates
6. Show scores
7. Show HIGH confidence suggestion
8. Planner approves
9. Persist actual progress
10. Dashboard updates
11. Audit trail shows complete chain

## Secondary journey
1. Upload ambiguous DPR
2. Get MEDIUM confidence
3. Show two close candidates
4. Planner edits/selects correct candidate
5. Audit records AI vs human final decision

## Third journey
1. Upload no-match DPR
2. System returns UNMATCHED
3. No schedule mutation
4. Planner can inspect and manually resolve or close it

## Error handling
Test:
- malformed Excel
- empty PDF
- PDF with no text
- LLM timeout
- embedding timeout
- DB unavailable
- duplicate upload
- duplicate approval
- invalid planner input

Frontend must show useful, human-readable errors.
Backend logs must include correlation/request ids if practical.

## Real-time refresh
"Real-time" for MVP means UI refresh or polling after committed updates.
Do not add websockets unless genuinely needed.

## Demo reset
Implement:
POST /api/demo/reset
It must restore deterministic seed state so every rehearsal starts identically.
