# PROMPT 06 — CORE MATCHING ENGINE

This is the most important engineering task.

Build the event-to-L5/L6 schedule matching engine as real application logic.

## Pipeline
FieldEvent
→ normalization
→ candidate retrieval
→ semantic similarity
→ discipline score
→ entity/equipment score
→ location/WBS score
→ temporal score
→ weighted final score
→ top-K
→ confidence tier

## Candidate retrieval
Do NOT compare every event with every activity once the dataset grows.
For the MVP:
- filter same project
- optionally filter compatible discipline
- use keyword/normalized-token prefilter
- then compute semantic score
- pgvector may be used where available

Keep retrieval modular.

## Semantic layer
Provider interface:
EmbeddingProvider.embed(text)

Provide:
- hosted embedding provider
- deterministic local fallback using TF-IDF / token similarity or another dependency-light method

This ensures offline demo operation.

## Signals
semantic_similarity:
0..1

discipline_match:
1 exact normalized match
0.5 compatible/unknown
0 mismatch

entity/equipment:
1 exact match
0.5 related/partial
0 mismatch
Use location/equipment evidence safely.

location/WBS:
1 exact
0.5 partial/parent relation
0 mismatch

temporal:
Use a soft score based on whether the event date is plausible relative to planned dates.
Do not punish post-completion events too aggressively because real reports can be late.

## Baseline score
final =
0.50*semantic
+0.15*discipline
+0.15*entity
+0.10*location_wbs
+0.10*temporal

Make weights configurable.

## Important improvement
Implement a rule that can override a superficially high score when a contradiction exists.
Examples:
- exact location conflict
- shop fabrication vs field erection mismatch
- discipline contradiction
- activity already completed far earlier and event clearly refers to different work

Never hardcode a hidden "correct answer" for the hero case.

## Confidence policy
Configurable thresholds:
HIGH if score >= configurable high threshold AND corroborating signals exist
MEDIUM if score >= medium threshold
LOW otherwise

Also use margin between rank 1 and rank 2:
- small margin can downgrade confidence
- a single high score is not enough if two candidates are nearly tied

No-match logic:
- if maximum score is too low
- or contradictions are too strong
then status = UNMATCHED

## Output
For each event return:
- top-K candidates
- every component score
- final score
- confidence tier
- rationale
- contradictions
- no-match explanation when applicable

## Hero case expected behavior
PIP-L6-0427 should rank first for:
"Spool erection near V-105 completed today. 14 spools installed."

Do NOT hardcode it.
It should win because of semantic + location + discipline evidence.

## Important demo quality
Also create an ambiguous example where the correct behavior is MEDIUM or LOW, and an unmatched example where the correct behavior is NO MATCH.

## Tests
Unit test every scoring signal.
Test:
- synonyms
- exact location
- wrong location
- wrong discipline
- no-match
- near-duplicate candidates
- ranking
- confidence downgrade by small margin
