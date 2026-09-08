# PROMPT 15 — FINAL AGENT HANDOFF + ACCEPTANCE TEST

Act as principal engineer.

Read:
- all prompt/context files
- repo README
- implementation
- test results
- evaluation.md
- final-mvp-status.md

Run the complete system from a clean state if possible.

Acceptance checklist:
[ ] backend starts
[ ] frontend starts
[ ] database works
[ ] seed works
[ ] schedule import works
[ ] DPR upload works
[ ] extraction works
[ ] matching works
[ ] top-K candidates visible
[ ] component scores visible
[ ] confidence routing works
[ ] HIGH requires/uses planner approval
[ ] MEDIUM requires review
[ ] LOW/UNMATCHED does not mutate schedule
[ ] approve persists update
[ ] edit persists chosen result
[ ] reject persists no schedule change
[ ] audit trail complete
[ ] dashboard reads committed values
[ ] duplicate approval is safe
[ ] hero case passes
[ ] ambiguous case passes
[ ] no-match case passes
[ ] offline fallback passes
[ ] tests pass
[ ] no fake metrics
[ ] no secret committed

Produce docs/acceptance-report.md with:
- date/time
- environment
- commands
- tests
- pass/fail
- measured metrics
- known limitations
- exact demo sequence

If anything fails, fix it before marking complete.
