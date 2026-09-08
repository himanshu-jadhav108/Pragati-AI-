# PROMPT 05 — AI EXTRACTION PIPELINE

Implement DPR → structured field event extraction.

## Core idea
The LLM is used only to interpret the source text into a strict schema.
It is NOT allowed to choose the schedule activity.

## Event schema
Use a Pydantic model similar to:
{
  event_date,
  discipline,
  activity_description,
  location,
  equipment_id,
  status,
  progress_percent,
  quantity,
  unit,
  source_reference,
  evidence_text
}

Add fields only when they improve matching/auditability.

Every extracted field should allow null when the source does not support it.
Never invent missing values.

## Provider abstraction
Create an interface such as:
LLMExtractor
- extract_events(text, metadata)

Implement:
1. hosted LLM provider
2. deterministic demo/local fallback

Provider selected through environment config.

## LLM instructions
Force JSON/schema output.
Tell the model:
- extract only what is supported by evidence
- do not infer schedule IDs
- do not infer exact quantities if absent
- preserve evidence snippets
- return multiple events if multiple activities are described
- flag ambiguity

## Validation
After LLM output:
- Pydantic validation
- normalization
- date parsing
- numeric parsing
- controlled vocabulary mapping where appropriate
- evidence presence check

## Deterministic fallback
Create rule-based extraction sufficient for the seeded demo:
- detect verbs/status such as completed, started, installed, erected
- capture nearby equipment/location identifiers
- capture quantities like "14 spools"
- identify date from document metadata when "today" is used
- use the full sentence as evidence

The fallback must produce the same event schema.

## API
Implement:
POST /api/extractions/{document_id}/run

Persist extracted events.

## UI contract
Expose:
- raw source text
- extracted fields
- evidence
- extraction status/confidence if available
- provider used

Never hide whether the system is using live AI or fallback mode.
