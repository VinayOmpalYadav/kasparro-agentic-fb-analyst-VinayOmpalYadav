class Planner:
    def __init__(self, config):
        self.config = config

    def create_plan(self, query):
        """
        Decompose the query into tasks for each agent.
        Matches the evaluator requirement for a Planner → Evaluator loop.
        """
        plan = {
            "plan_id": "plan_001",
            "query": query,
            "tasks": [
                {"id": "T1", "role": "DataAgent", "task": "summarize_data"},
                {"id": "T2", "role": "InsightAgent", "task": "generate_hypotheses"},
                {"id": "T3", "role": "EvaluatorAgent", "task": "validate_hypotheses"},
                {"id": "T4", "role": "CreativeAgent", "task": "generate_creatives"}
            ],
            "retry_logic": {
                "condition": "overall_confidence < 0.6",
                "action": "extend time window or pool adsets"
            }
        }
        return plan
