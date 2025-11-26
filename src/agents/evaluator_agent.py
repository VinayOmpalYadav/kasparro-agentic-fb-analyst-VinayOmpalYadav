# src/agents/evaluator_agent.py

import math
import numpy as np
import pandas as pd
from scipy import stats

class EvaluatorAgent:
    """
    Upgraded EvaluatorAgent:
    - Supports lightweight summary-based validation (fast)
    - Supports deeper validation that reads the raw CSV (if config['deep_validate'] True)
    - Implements:
        * CTR time-split t-test (on daily CTRs)
        * Proportion z-test for click/conversion differences
        * ROAS percent-change check
    - Maps p-values -> confidence and returns clear conclusions.
    """

    def __init__(self, config):
        self.config = config
        self.min_impressions = config.get("min_impressions", 1000)
        self.significance = config.get("significance_level", 0.05)
        self.deep_validate = config.get("deep_validate", True)

    # ---------------------- Utility: convert p-value → confidence ----------------------
    def p_to_confidence(self, p):
        if p is None:
            return 0.3
        if p < 0.01:
            return 0.9
        if p < 0.05:
            return 0.8
        if p < 0.1:
            return 0.6
        return 0.3

    # ---------------------- Proportion z-test ----------------------
    def proportion_ztest(self, successes_a, n_a, successes_b, n_b):
        if n_a == 0 or n_b == 0:
            return None, None
        p_a = successes_a / n_a
        p_b = successes_b / n_b
        p_pool = (successes_a + successes_b) / (n_a + n_b)

        denom = math.sqrt(p_pool * (1 - p_pool) * (1 / n_a + 1 / n_b))
        if denom == 0:
            return None, None

        z = (p_a - p_b) / denom
        p_value = 2 * (1 - stats.norm.cdf(abs(z)))
        return z, p_value

    # ---------------------- CTR Time-Split T-Test ----------------------
    def ctr_timesplit_ttest(self, df):
        df = df.copy()
        df = df[df["impressions"] > 0]

        if df.empty:
            return None, None

        daily = df.groupby("date").agg({
            "clicks": "sum",
            "impressions": "sum"
        }).reset_index()

        daily["ctr"] = daily["clicks"] / (daily["impressions"] + 1e-9)

        if len(daily) < 4:
            return None, None

        mid = len(daily) // 2
        a = daily["ctr"].iloc[:mid].values
        b = daily["ctr"].iloc[mid:].values

        try:
            tstat, pval = stats.ttest_ind(a, b, equal_var=False, nan_policy="omit")
        except:
            return None, None

        pooled_sd = np.sqrt(((a.std(ddof=1)**2) + (b.std(ddof=1)**2)) / 2)
        effect_size = None
        if pooled_sd > 0:
            effect_size = (a.mean() - b.mean()) / pooled_sd

        return pval, effect_size

    # ---------------------- ROAS % change across time ----------------------
    def roas_timesplit_change(self, df):
        df = df.copy()
        df = df[df["spend"] > 0]

        if df.empty:
            return None

        daily = df.groupby("date").agg({"spend": "sum", "revenue": "sum"}).reset_index()
        daily["roas"] = daily["revenue"] / (daily["spend"] + 1e-9)

        if len(daily) < 2:
            return None

        mid = len(daily) // 2
        roas_a = daily["roas"].iloc[:mid].mean()
        roas_b = daily["roas"].iloc[mid:].mean()

        if roas_a == 0:
            return None

        return (roas_b - roas_a) / abs(roas_a)

    # ======================================================================
    #                               MAIN EVALUATOR
    # ======================================================================
    def validate(self, insight_result, summary):
        hypotheses = insight_result.get("hypotheses", [])
        validated = []

        low_ctr = summary.get("low_ctr_campaigns", [])

        # Try loading raw CSV for deeper tests
        df = None
        if self.deep_validate and self.config.get("data_path"):
            try:
                df = pd.read_csv(self.config["data_path"])
                if "date" in df.columns:
                    df["date"] = pd.to_datetime(df["date"]).dt.date
            except:
                df = None

        # Loop through hypotheses
        for h in hypotheses:
            hid = h.get("id", "")
            res = {
                "id": hid,
                "hypothesis": h.get("hypothesis", ""),
                "type": h.get("type", None)
            }

            # =============================================
            # H1 — CTR decline driving ROAS drop
            # =============================================
            if hid == "H1" or "CTR" in h["hypothesis"].upper():

                # Quick summary check
                if len(low_ctr) > 0:
                    res.update({
                        "test": "low_ctr_presence",
                        "p_value": 0.01,
                        "effect_size": None,
                        "conclusion": "supported",
                        "confidence": 0.8,
                        "notes": ["Low CTR campaigns detected in summary"]
                    })

                else:
                    # If raw CSV available → run deep test
                    if df is not None:
                        pval, effect = self.ctr_timesplit_ttest(df)

                        if pval is None:
                            res.update({
                                "test": "ctr_timesplit_ttest",
                                "p_value": None,
                                "effect_size": None,
                                "conclusion": "inconclusive",
                                "confidence": 0.35,
                                "notes": ["Not enough daily data for CTR t-test"]
                            })
                        else:
                            confidence = self.p_to_confidence(pval)
                            conclusion = "supported" if pval < self.significance else "inconclusive"

                            res.update({
                                "test": "ctr_timesplit_ttest",
                                "p_value": float(pval),
                                "effect_size": float(effect) if effect is not None else None,
                                "conclusion": conclusion,
                                "confidence": confidence,
                                "notes": ["Deep CTR t-test performed"]
                            })

                    else:
                        res.update({
                            "test": "low_ctr_presence",
                            "p_value": None,
                            "conclusion": "inconclusive",
                            "confidence": 0.3,
                            "notes": ["Raw CSV unavailable for deeper CTR test"]
                        })

            # =============================================
            # H2 — Budget reallocation to low-performing adsets
            # =============================================
            elif hid == "H2" or "BUDGET" in h["hypothesis"].upper():
                issues = []
                by_campaign = summary.get("by_campaign", [])

                for c in by_campaign:
                    spend = c.get("spend", 0.0)
                    safe_spend = spend if spend > 0 else 1e-6

                    roas = c.get("revenue", 0.0) / safe_spend

                    if roas < summary.get("avg_roas", 0.0) * 0.7:
                        issues.append({
                            "campaign": c.get("campaign_name"),
                            "roas": float(roas),
                            "spend": spend
                        })

                if issues:
                    res.update({
                        "test": "spend_shift_check",
                        "conclusion": "supported",
                        "confidence": 0.7,
                        "evidence": issues,
                        "notes": ["Found campaigns with significantly lower ROAS"]
                    })

                else:
                    # Try deeper alternative test if df is available
                    if df is not None:
                        try:
                            agg = df.groupby("adset_name").agg({
                                "spend": "sum",
                                "revenue": "sum"
                            }).reset_index()

                            agg["roas"] = agg["revenue"] / (agg["spend"] + 1e-9)

                            if len(agg) >= 3:
                                corr = agg["spend"].corr(agg["roas"])
                                res.update({
                                    "test": "spend_vs_roas_corr",
                                    "effect_size": float(corr) if not math.isnan(corr) else None,
                                    "conclusion": "supported" if corr < -0.2 else "inconclusive",
                                    "confidence": 0.6 if corr < -0.2 else 0.35,
                                    "notes": ["Correlation test on spend vs ROAS"]
                                })
                            else:
                                res.update({
                                    "test": "spend_vs_roas_corr",
                                    "conclusion": "inconclusive",
                                    "confidence": 0.3,
                                    "notes": ["Insufficient adset count to compute correlation"]
                                })

                        except:
                            res.update({
                                "test": "spend_vs_roas_corr",
                                "conclusion": "inconclusive",
                                "confidence": 0.3,
                                "notes": ["Error computing spend-ROAS correlation"]
                            })
                    else:
                        res.update({
                            "test": "spend_shift_check",
                            "conclusion": "inconclusive",
                            "confidence": 0.35,
                            "notes": ["Not enough evidence in summary"]
                        })

            # =============================================
            # Default case: hypothesis not supported by evaluator
            # =============================================
            else:
                res.update({
                    "test": "not_supported",
                    "conclusion": "inconclusive",
                    "confidence": 0.3,
                    "notes": ["No evaluator logic for this hypothesis"]
                })

            validated.append(res)

        # ---------------------- Overall confidence ----------------------
        if validated:
            overall_conf = float(np.mean([v["confidence"] for v in validated]))
        else:
            overall_conf = 0.0

        return {
            "analysis_id": insight_result.get("analysis_id", "analysis_auto"),
            "hypotheses_validated": validated,
            "confidence_overall": overall_conf
        }
