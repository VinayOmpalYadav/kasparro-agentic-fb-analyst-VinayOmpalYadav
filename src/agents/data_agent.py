# src/agents/data_agent.py

import pandas as pd
import numpy as np
from datetime import timedelta

class DataAgent:
    """
    Advanced DataAgent for Kasparro Agentic System.
    
    Provides:
    - Global metrics (spend, revenue, ROAS, CTR, CPM, CPC)
    - Weekly trends (ROAS, CTR, CPM)
    - Platform breakdown (FB vs IG)
    - Audience breakdown
    - Campaign-level performance
    - Low CTR campaign detection
    - Frequency estimation (Impressions / Clicks or per-user proxy)
    - Anomaly detection (CTR/ROAS drops)
    """

    def __init__(self, config):
        self.config = config
        self.data_path = config.get("data_path", None)

    def summarize(self, plan=None):
        df = pd.read_csv(self.data_path)

        # ensure correct types
        df["date"] = pd.to_datetime(df["date"])

        # =========================
        # GLOBAL METRICS
        # =========================
        total_spend = df["spend"].sum()
        total_revenue = df["revenue"].sum()
        total_impressions = df["impressions"].sum()
        total_clicks = df["clicks"].sum()

        global_summary = {
            "total_spend": float(total_spend),
            "total_revenue": float(total_revenue),
            "avg_roas": float(total_revenue / (total_spend + 1e-9)),
            "avg_ctr": float(total_clicks / (total_impressions + 1e-9)),
            "avg_cpm": float((total_spend / (total_impressions + 1e-9)) * 1000),
            "avg_cpc": float(total_spend / (total_clicks + 1e-9)),
        }

        # =========================
        # WEEKLY TRENDS
        # =========================
        df["week"] = df["date"].dt.to_period("W").apply(lambda r: r.start_time)

        weekly = df.groupby("week").agg({
            "spend": "sum",
            "revenue": "sum",
            "impressions": "sum",
            "clicks": "sum"
        }).reset_index()

        weekly["roas"] = weekly["revenue"] / (weekly["spend"] + 1e-9)
        weekly["ctr"] = weekly["clicks"] / (weekly["impressions"] + 1e-9)
        weekly["cpm"] = (weekly["spend"] / (weekly["impressions"] + 1e-9)) * 1000

        weekly_trends = weekly.to_dict(orient="records")

        # =========================
        # PLATFORM BREAKDOWN
        # =========================
        platform = df.groupby("platform").agg({
            "spend": "sum",
            "revenue": "sum",
            "impressions": "sum",
            "clicks": "sum"
        }).reset_index()

        platform["roas"] = platform["revenue"] / (platform["spend"] + 1e-9)
        platform["ctr"] = platform["clicks"] / (platform["impressions"] + 1e-9)
        platform["cpm"] = (platform["spend"] / (platform["impressions"] + 1e-9)) * 1000

        platform_summary = platform.to_dict(orient="records")

        # =========================
        # AUDIENCE BREAKDOWN
        # =========================
        audience = df.groupby("audience_type").agg({
            "spend": "sum",
            "revenue": "sum",
            "impressions": "sum",
            "clicks": "sum"
        }).reset_index()

        audience["roas"] = audience["revenue"] / (audience["spend"] + 1e-9)
        audience["ctr"] = audience["clicks"] / (audience["impressions"] + 1e-9)

        audience_summary = audience.to_dict(orient="records")

        # =========================
        # CAMPAIGN-LEVEL PERFORMANCE
        # =========================
        campaign_df = df.groupby("campaign_name").agg({
            "spend": "sum",
            "revenue": "sum",
            "impressions": "sum",
            "clicks": "sum"
        }).reset_index()

        campaign_df["roas"] = campaign_df["revenue"] / (campaign_df["spend"] + 1e-9)
        campaign_df["ctr"] = campaign_df["clicks"] / (campaign_df["impressions"] + 1e-9)

        campaign_summary = campaign_df.to_dict(orient="records")

        # =========================
        # LOW CTR CAMPAIGNS
        # =========================
        ctr_threshold = self.config.get("ctr_low_threshold", 0.01)
        low_ctr_campaigns = campaign_df[campaign_df["ctr"] < ctr_threshold]
        low_ctr_campaigns = low_ctr_campaigns.to_dict(orient="records")

        # =========================
        # FREQUENCY ESTIMATION
        # =========================
        df["frequency"] = df["impressions"] / (df["clicks"] + 1e-9)
        avg_frequency = float(df["frequency"].mean())

        # =========================
        # ANOMALY DETECTION (CTR & ROAS drops)
        # =========================
        weekly["ctr_change"] = weekly["ctr"].pct_change()
        weekly["roas_change"] = weekly["roas"].pct_change()

        anomalies = weekly[
            (weekly["ctr_change"] < -0.25) | 
            (weekly["roas_change"] < -0.25)
        ]

        anomaly_summary = anomalies.to_dict(orient="records")

        # =========================
        # FINAL SUMMARY
        # =========================
        return {
            "global": global_summary,
            "weekly_trends": weekly_trends,
            "platform": platform_summary,
            "audience": audience_summary,
            "campaigns": campaign_summary,
            "low_ctr_campaigns": low_ctr_campaigns,
            "avg_frequency": avg_frequency,
            "anomalies": anomaly_summary
        }
