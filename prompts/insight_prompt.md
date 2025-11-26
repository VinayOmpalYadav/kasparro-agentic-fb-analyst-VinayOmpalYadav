# Insight Agent Prompt

## Objective
Generate hypotheses explaining ROAS changes using the summarized dataset.

## Required Output (list of hypotheses)
[
  {
    "id": "H1",
    "hypothesis": "text",
    "mechanism": "why this affects ROAS",
    "evidence_needed": ["metric1", "metric2"],
    "initial_confidence": 0.0–1.0
  }
]

## Reasoning Format
Think → Identify Patterns → Generate Hypotheses → Prioritize → Conclude

## Constraints
- Each hypothesis must reference a real metric.
- Must include causal direction (increase/decrease).
- Must include required evidence for evaluator.

## Reflection
If hypotheses < 3, broaden search space.
