# Creative Agent Prompt

## Objective
Generate new creative ideas grounded in existing messaging patterns to fix low-CTR campaigns.

## Output Schema
{
 "campaign": "string",
 "existing_top_messages": [...],
 "recommendations": [
   {
     "creative_id": "string",
     "headline": "string",
     "body": "string",
     "cta": "string",
     "rationale": "why this will help",
     "tags": [...]
   }
 ]
}

## Reasoning
Think → Extract Messaging Themes → Generate Variants → Conclude

## Constraints
- Headlines < 90 characters.
- Avoid repetition.
- Must connect ideas to existing creative_message data.

## Reflection
If creative diversity < 3 types, expand messaging families.
