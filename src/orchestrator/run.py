#!/usr/bin/env python3

import argparse, json, yaml, os
from pathlib import Path

from src.utils.logger import StructuredLogger
from src.agents.planner import Planner
from src.agents.data_agent import DataAgent
from src.agents.insight_agent import InsightAgent
from src.agents.evaluator_agent import EvaluatorAgent
from src.agents.creative_agent import CreativeAgent
from src.orchestrator.build_report import ReportBuilder

logger = StructuredLogger()   # logger for JSON logs


def main(query):
    # ---- LOAD CONFIG ----
    config = yaml.safe_load(open("config/config.yaml"))

    # ---- START LOG ----
    logger.info("run_start", {"query": query})

    # ---- PLANNER ----
    planner = Planner(config)
    plan = planner.create_plan(query)
    logger.info("plan_created", plan)

    # ---- DATA AGENT ----
    data_agent = DataAgent(config)
    summary = data_agent.summarize(plan)
    logger.info("data_summary", {"summary_keys": list(summary.keys())})

    # ---- INSIGHT AGENT ----
    insight_agent = InsightAgent(config)
    insight_result = insight_agent.generate(summary, plan)
    logger.info("insights_generated", {"count": len(insight_result["hypotheses"])})

    # ---- EVALUATOR AGENT ----
    evaluator = EvaluatorAgent(config)
    evaluated = evaluator.validate(insight_result, summary)
    logger.info("hypotheses_validated", {"confidence": evaluated["confidence_overall"]})

    # ---- CREATIVE AGENT ----
    creative_agent = CreativeAgent(config)
    creatives = creative_agent.generate(summary, evaluated)
    logger.info("creatives_generated", {"count": len(creatives)})

    # ---- REPORT BUILDER ----
    report_builder = ReportBuilder(config)
    report_path = report_builder.build(summary, insight_result, evaluated, creatives)
    logger.info("report_generated", {"path": report_path})

    # ---- SAVE OUTPUTS ----
    os.makedirs("reports", exist_ok=True)

    Path(config["outputs"]["insights"]).write_text(json.dumps(evaluated, indent=2))
    Path(config["outputs"]["creatives"]).write_text(json.dumps(creatives, indent=2))

    # Report already saved by ReportBuilder

    logger.info("run_complete", {
        "insights_path": config["outputs"]["insights"],
        "creatives_path": config["outputs"]["creatives"],
        "report_path": report_path
    })

    # ---- PRINT TO TERMINAL ----
    print("Analysis complete.")
    print("Insights →", config["outputs"]["insights"])
    print("Creatives →", config["outputs"]["creatives"])
    print("Report →", config["outputs"]["report"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    args = parser.parse_args()
    main(args.query)
