# src/orchestrator/build_report.py

import json
from pathlib import Path
from datetime import datetime

class ReportBuilder:

    def __init__(self, config):
        self.config = config

    def build(self, summary, insights, evaluated, creatives):
        """
        Generates a full markdown report for marketers.
        """

        global_stats = summary["global"]
        weekly = summary["weekly_trends"]
        anomalies = summary["anomalies"]

        md = []

        # ======================
        # Header
        # ======================
        md.append("# 📊 Facebook Ads Performance Report")
        md.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        md.append("---")

        # ======================
        # Executive Summary
        # ======================
        md.append("## 🔍 Executive Summary")
        md.append(
            f"- **Total Spend:** ${global_stats['total_spend']:.2f}\n"
            f"- **Revenue:** ${global_stats['total_revenue']:.2f}\n"
            f"- **ROAS:** {global_stats['avg_roas']:.2f}\n"
            f"- **CTR:** {global_stats['avg_ctr']:.4f}\n"
            f"- **CPM:** ${global_stats['avg_cpm']:.2f}\n"
        )

        if anomalies:
            md.append("⚠️ **Performance anomalies detected in recent weeks:**")
            for a in anomalies:
                md.append(f"- Week starting **{a['week']}**: ROAS or CTR dropped >25%")

        md.append("---")

        # ======================
        # Hypotheses
        # ======================
        md.append("## 🧠 Key Hypotheses Generated")
        for h in insights["hypotheses"]:
            md.append(f"### {h['id']} — {h['hypothesis']}")
            md.append(f"- **Mechanism:** {h['mechanism']}")
            md.append(f"- **Evidence Needed:** {', '.join(h['evidence_needed'])}")
            md.append(f"- **Initial Confidence:** {h['initial_confidence']:.2f}\n")

        md.append("---")

        # ======================
        # Validation Results
        # ======================
        md.append("## 🧪 Evaluator Validation Results")
        for v in evaluated["hypotheses_validated"]:
            md.append(f"### {v['id']} — {v['hypothesis']}")
            md.append(f"- **Test:** {v['test']}")
            md.append(f"- **Conclusion:** {v['conclusion']}")
            md.append(f"- **Confidence:** {v['confidence']:.2f}")
            if v.get("p_value") is not None:
                md.append(f"- **p-value:** {v['p_value']}")
            if v.get("evidence"):
                md.append(f"- **Evidence:** {v['evidence']}")
            md.append("")

        md.append(f"### ⭐ Overall Confidence Score: {evaluated['confidence_overall']:.2f}")

        md.append("---")

        # ======================
        # Creative Recommendations
        # ======================
        md.append("## 🎨 Creative Recommendations")

        for c in creatives:
            md.append(f"### Campaign: {c['campaign']}")
            md.append("Top new creative ideas:")

            for r in c["recommendations"][:3]:   # top 3 per campaign
                md.append(f"- **Headline:** {r['headline']}")
                md.append(f"  - Style: {r['style']}")
                md.append(f"  - CTA: {r['cta']}")
                md.append(f"  - Confidence: {r['confidence']}")
                md.append(f"  - Rationale: {r['rationale']}")

            md.append("")

        md.append("---")

        # ======================
        # Suggested Actions
        # ======================
        md.append("## 🚀 Recommended Next Steps")
        md.append("- Shift spend toward high-ROAS platforms/adsets")
        md.append("- Refresh fatigued creatives with the above recommendations")
        md.append("- Run A/B tests on CTR-driven creatives")
        md.append("- Monitor frequency & CPM weekly to detect wear-out early")
        md.append("- Use evaluator confidence score to prioritize fixes")

        md.append("---")

        # ======================
        # Save File
        # ======================
        out_path = Path(self.config["outputs"]["report"])
        Path("reports").mkdir(exist_ok=True)
        out_path.write_text("\n".join(md))

        return str(out_path)
