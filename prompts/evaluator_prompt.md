# Evaluator Agent Prompt

## Objective
Quantitatively validate hypotheses using statistical tests.

## Required Output
{
  "hypothesis_id": "H1",
  "test": "t-test / chi-square / trend",
  "p_value": number,
  "effect_size": number,
  "confidence": number,
  "conclusion": "supported / not_supported / inconclusive"
}

## Reasoning Structure
Think → Test Selection → Execute → Interpret → Conclude

## Requirements
- Map p-values to confidence.
- Use minimum impressions threshold.
- If insufficient data → mark "inconclusive".

## Reflection
If results contradictory → retry with aggregated windows.
