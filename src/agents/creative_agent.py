# src/agents/creative_agent.py

import re
import random
from collections import Counter, defaultdict
from pathlib import Path
import pandas as pd

# small stopword set (keeps dependencies minimal)
STOPWORDS = {
    "the","and","for","with","our","your","this","that","from","have","has","are",
    "is","in","on","to","of","a","an","by","be","it","we","you","its","as"
}

def tokenize(text):
    text = text.lower()
    # keep alphanum and spaces
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    toks = [t for t in text.split() if t and t not in STOPWORDS and len(t) > 2]
    return toks

def top_phrases(messages, n=10):
    # returns top single tokens and simple bigrams
    cnt = Counter()
    big = Counter()
    for m in messages:
        toks = tokenize(m)
        cnt.update(toks)
        big.update([f"{toks[i]} {toks[i+1]}" for i in range(len(toks)-1)]) if len(toks) > 1 else None
    # combine tokens and bigrams but keep tag
    tokens_top = [t for t,_ in cnt.most_common(n)]
    big_top = [b for b,_ in big.most_common(min(n, len(big)))]
    return tokens_top, big_top

class CreativeAgent:
    def __init__(self, config):
        self.config = config
        self.random_seed = config.get("seed", 42)
        random.seed(self.random_seed)
        self.data_path = config.get("data_path", None)

    def _load_messages_for_campaign(self, campaign):
        if not self.data_path:
            return []
        try:
            df = pd.read_csv(self.data_path)
        except Exception:
            return []
        dfc = df[df["campaign_name"] == campaign]
        if "creative_message" not in dfc.columns:
            return []
        msgs = dfc["creative_message"].dropna().astype(str).tolist()
        return msgs

    def _estimate_confidence(self, msg_count):
        # more messages -> higher confidence
        if msg_count >= 10:
            return 0.75
        if msg_count >= 5:
            return 0.6
        if msg_count >= 2:
            return 0.45
        return 0.25

    def _make_candidates(self, campaign, top_tokens, top_bigrams, existing_msgs, conf_base):
        # build 6 candidates with different styles
        candidates = []

        # Helper templates (kept short)
        templates = [
            ("Benefit", "{token} for all-day comfort", "Lightweight design + proven comfort. Try now.", "Shop now"),
            ("Urgency", "Limited time: {bigram} — ends soon", "Hurry, limited stock. Get yours before they sell out.", "Buy now"),
            ("SocialProof", "Loved by thousands: {token}", "Join thousands who chose {token}. Free returns.", "Shop trusted"),
            ("Discount", "{token} — Save 20% today", "Exclusive offer — limited period discount.", "Get 20% off"),
            ("Feature", "Engineered: {bigram}", "Advanced features that deliver comfort and performance.", "Learn more"),
            ("FOMO", "Don't miss {token}", "Customers are buying fast — secure yours today.", "Shop now")
        ]

        # ensure we have fillers
        filler_token = top_tokens[0] if top_tokens else "comfort"
        filler_bigram = top_bigrams[0] if top_bigrams else filler_token + " fit"

        for style, htmp, btmp, cta in templates:
            headline = htmp.format(token=filler_token.title(), bigram=filler_bigram.title())
            body = btmp.format(token=filler_token)
            candidate = {
                "creative_id": f"{campaign}_{style}",
                "style": style,
                "headline": headline,
                "body": body,
                "cta": cta,
                "rationale": f"Derived from top themes: tokens={top_tokens[:3]} bigrams={top_bigrams[:3]}",
                "expected_outcome": "Increase CTR by ~0.3-1.0% (estimate)",
                "confidence": min(0.95, round(conf_base + random.uniform(-0.1, 0.1), 2)),
                "tags": [style.lower(), filler_token]
            }
            candidates.append(candidate)

        return candidates

    def generate(self, summary, evaluated):
        """
        summary: output of DataAgent (with low_ctr_campaigns etc.)
        evaluated: validated hypotheses (not used heavily here but could influence tone)
        """
        recs = []
        low = summary.get("low_ctr_campaigns", [])
        # If no low-CTR campaigns, we still inspect top campaigns for opportunistic creatives
        campaigns_to_consider = [c.get("campaign_name") for c in low] if low else \
                                [c.get("campaign_name") for c in summary.get("campaigns", [])][:3]

        if not campaigns_to_consider:
            return [{"note": "no campaigns available for creative generation"}]

        for campaign in campaigns_to_consider:
            msgs = self._load_messages_for_campaign(campaign)
            tokens, bigrams = top_phrases(msgs, n=10)
            conf_base = self._estimate_confidence(len(msgs))
            candidates = self._make_candidates(campaign, tokens, bigrams, msgs, conf_base)

            recs.append({
                "analysis_id": evaluated.get("analysis_id", "analysis_auto"),
                "campaign": campaign,
                "existing_top_messages": msgs[:10],
                "recommendations": candidates,
                "notes": ["generated using token/bigram extraction", f"messages_count={len(msgs)}"]
            })

        return recs
