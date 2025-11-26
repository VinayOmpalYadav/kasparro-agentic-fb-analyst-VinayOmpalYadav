# tests/test_evaluator.py
import pytest
from src.agents.evaluator_agent import EvaluatorAgent

# Basic config (uses deep_validate False to keep tests deterministic)
config = {
    "ctr_low_threshold": 0.01,
    "roas_drop_threshold": 0.15,
    "min_impressions": 100,
    "significance_level": 0.05,
    "deep_validate": False  # use summary-based fast path in unit tests
}

def test_evaluator_supports_ctr_hypothesis_quick():
    evaluator = EvaluatorAgent(config)

    insight_result = {
        "analysis_id": "analysis_001",
        "hypotheses": [
            {"id": "H1", "hypothesis": "CTR decline is driving ROAS drop."}
        ]
    }

    summary = {
        "avg_roas": 2.0,
        "by_campaign": [],
        "low_ctr_campaigns": [
            {"campaign_name": "TestCampaign", "ctr": 0.005}
        ]
    }

    result = evaluator.validate(insight_result, summary)
    v = result["hypotheses_validated"][0]
    assert v["id"] == "H1"
    assert v["conclusion"] == "supported"
    assert v["confidence"] >= 0.7

def test_evaluator_inconclusive_when_no_low_ctr_quick():
    evaluator = EvaluatorAgent(config)

    insight_result = {
        "analysis_id": "analysis_002",
        "hypotheses": [
            {"id": "H1", "hypothesis": "CTR decline is driving ROAS drop."}
        ]
    }

    summary = {
        "avg_roas": 2.0,
        "by_campaign": [],
        "low_ctr_campaigns": []
    }

    result = evaluator.validate(insight_result, summary)
    v = result["hypotheses_validated"][0]
    assert v["conclusion"] == "inconclusive"
    assert v["confidence"] <= 0.5

def test_evaluator_budget_shift_detects_low_roas():
    evaluator = EvaluatorAgent(config)

    insight_result = {
        "analysis_id": "analysis_003",
        "hypotheses": [
            {"id": "H2", "hypothesis": "Budget reallocated to low-performing adsets"}
        ]
    }

    summary = {
        "avg_roas": 3.0,
        "by_campaign": [
            {"campaign_name": "A", "spend": 1000, "revenue": 400, "ctr": 0.02},  # roas 0.4
            {"campaign_name": "B", "spend": 200, "revenue": 300, "ctr": 0.05}    # roas 1.5
        ],
        "low_ctr_campaigns": []
    }

    result = evaluator.validate(insight_result, summary)
    v = result["hypotheses_validated"][0]
    assert v["conclusion"] == "supported"
    assert v["confidence"] >= 0.6
