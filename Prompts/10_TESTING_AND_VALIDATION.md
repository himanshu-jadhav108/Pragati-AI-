# PROMPT 10 — TESTS + MEASURED VALIDATION

Do not claim model accuracy until tests are actually run.

## Automated tests

### Backend
- API health
- imports
- extraction schema validation
- matching signals
- ranking
- confidence thresholds
- approval transaction
- audit trail
- idempotency

### Frontend
At minimum smoke-test critical routes/components where tooling allows.

### End-to-end
At least:
1. hero success case
2. ambiguous review case
3. unmatched case
4. reject case
5. edit-and-approve case

## Metrics
Compute on the ground-truth synthetic set:
- Top-1 match accuracy
- Top-3 recall
- extraction field accuracy
- unmatched detection precision/recall where labels exist
- human correction rate in simulation
- processing time
- schedule update latency
- audit completeness

## Reporting rule
Write:
docs/evaluation.md

Separate:
- Prototype Target
- Measured Result
- Dataset Description
- Test Method
- Limitations

Never write "achieved 90%" unless the test produced 90%.

## Matching evaluation
Use ground_truth.csv.
For each event:
- compare top-1 activity id
- check whether ground truth appears in top 3
- identify false confident matches
- analyze failures by reason

## Confidence calibration
Produce a simple table:
confidence tier
count
correct
incorrect
accuracy

A good system should have substantially higher correctness in HIGH than LOW, but report whatever the measurements show.

## Regression tests
Save the hero event and important edge cases as fixtures.
Future code changes must not break them.

## Definition of done
One command or documented sequence runs the core tests.
Fix failures before declaring MVP complete.
