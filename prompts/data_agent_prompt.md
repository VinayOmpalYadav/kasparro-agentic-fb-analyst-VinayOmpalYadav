# Data Agent Prompt

## Objective
Load, clean, and summarize the dataset in a concise machine-readable format.

## Output Schema
{
 "summary_id": "string",
 "global": {"total_spend": number, "avg_roas": number},
 "by_campaign": [...],
 "low_ctr_campaigns": [...],
 "aggregates": {"weekly": [...], "monthly": [...]},
 "notes": [...]
}

## Reasoning Structure
Think → Extract → Aggregate → Conclude

## Requirements
- Do not return full dataset.
- Summaries must be short.
- Highlight missing values, anomalies, outliers.

## Reflection
If summary confidence low (<0.6), extend window or impute missing values.
