# src/agents/insight_agent.py

import numpy as np

class InsightAgent:
    """
    Advanced InsightAgent for Kasparro Agentic System.

    Produces 4–6 grounded, data-driven hypotheses using:
    - CTR trends
    - ROAS trends
    - CPM & CPC changes
    - Audience fatigue (via frequency)
    - Platform underperformance
    - Creative fatigue (low CTR campaigns)
    - Anomaly detection (weekly ROAS/CTR drops)
    """

    def __init__(self, config):
        self.config = config

    def generate(self, summary, plan=None):

        global_stats = summary["global"]
        weekly = summary["weekly_trends"]
        platform = summary["platform"]
        audience = summary["audience"]
        low_ctr = summary["low_ctr_campaigns"]
        freq = summary["avg_frequency"]
        anomalies = summary["anomalies"]

        hypotheses = []

        # Helper for extracting trends
        def trend(series):
            if len(series) < 2:
                return 0
            return (series[-1] - series[0]) / (abs(series[0]) + 1e-6)

        # ============================
        # H1 – CTR Decline → ROAS Drop
        # ============================
        ctr_series = [w["ctr"] for w in weekly]
        ctr_trend = trend(ctr_series)

        if ctr_trend < -0.10 or len(low_ctr) > 0:
            hypotheses.append({
                "id": "H1",
                "hypothesis": "CTR decline is contributing to ROAS drop.",
                "mechanism": "Lower CTR reduces traffic entering the funnel, lowering overall purchase volume.",
                "evidence_needed": [
                    "CTR trend t-test",
                    "Click-volume proportion z-test"
                ],
                "initial_confidence": 0.7 if len(low_ctr) > 0 else 0.55,
                "type": "performance"
            })

        # ============================
        # H2 – Audience Fatigue (High Frequency)
        # ============================
        if freq > 4.0:
            hypotheses.append({
                "id": "H2",
                "hypothesis": "Audience fatigue is causing performance decline.",
                "mechanism": "High ad frequency reduces novelty, increasing CPC and reducing CTR.",
                "evidence_needed": [
                    "Frequency trend across time",
                    "CTR decline correlating with frequency rise"
                ],
                "initial_confidence": 0.6,
                "type": "audience"
            })

        # ============================
        # H3 – Rising CPM (Cost per 1000 impressions)
        # ============================
        cpm_series = [w["cpm"] for w in weekly]
        cpm_trend = trend(cpm_series)

        if cpm_trend > 0.1:
            hypotheses.append({
                "id": "H3",
                "hypothesis": "Rising CPM is increasing acquisition costs.",
                "mechanism": "Higher CPM increases traffic costs, reducing ROAS unless conversion rate increases.",
                "evidence_needed": ["CPM trend significance", "Spend-to-impressions ratio check"],
                "initial_confidence": 0.55,
                "type": "cost"
            })

        # ============================
        # H4 – Platform Shift (FB vs IG)
        # ============================
        if len(platform) >= 2:
            worst_platform = None
            for p in platform:
                if worst_platform is None or p["roas"] < worst_platform["roas"]:
                    worst_platform = p

            hypotheses.append({
                "id": "H4",
                "hypothesis": f"{worst_platform['platform']} placements underperform relative to others.",
                "mechanism": "Platform-level algorithm or audience mismatch reduces conversion efficiency.",
                "evidence_needed": ["Platform ROAS comparison", "CTR comparison"],
                "initial_confidence": 0.5,
                "type": "platform"
            })

        # ============================
        # H5 – Creative Fatigue (Low CTR Campaigns)
        # ============================
        if len(low_ctr) > 0:
            hypotheses.append({
                "id": "H5",
                "hypothesis": "Creative fatigue is lowering engagement.",
                "mechanism": "Users have stopped responding to current creatives; CTR falls with repetition.",
                "evidence_needed": ["Creative message analysis", "CTR decline for specific creative IDs"],
                "initial_confidence": 0.65,
                "type": "creative"
            })

        # ============================
        # H6 – Anomaly Detected (Sharp CTR/ROAS Drop)
        # ============================
        if len(anomalies) > 0:
            hypotheses.append({
                "id": "H6",
                "hypothesis": "Abrupt performance anomaly detected in recent weeks.",
                "mechanism": "Possible budget shift, tracking issue, or competitor surge.",
                "evidence_needed": ["DEEP evaluator: ROAS & CTR time-split tests"],
                "initial_confidence": 0.6,
                "type": "anomaly"
            })

        # If no hypotheses generated, fallback
        if len(hypotheses) == 0:
            hypotheses.append({
                "id": "H0",
                "hypothesis": "No strong signals detected; performance variation could be noise.",
                "mechanism": "Metrics stable with no meaningful trends.",
                "evidence_needed": ["General correlation tests"],
                "initial_confidence": 0.3,
                "type": "fallback"
            })

        return {
            "analysis_id": "analysis_auto",
            "hypotheses": hypotheses
        }
