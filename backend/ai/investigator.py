"""
backend/ai/investigator.py

AI Investigator: accepts a Phase 2 discovery dict and asks Gemini Flash
WHY the pattern exists and WHAT to do about it.

Rules:
- Sends only structured evidence to the LLM, NOT the raw CSV.
- Uses cautious language ("associated with", "likely", "evidence suggests").
- Falls back to deterministic analysis if LLM fails or returns invalid JSON.
- Returns a validated Pydantic model.
"""
from __future__ import annotations

import json
import os
import urllib.request
import urllib.error
from typing import List

from pydantic import BaseModel, Field, field_validator


# ── Pydantic output schema ─────────────────────────────────────────────────

class InvestigationResult(BaseModel):
    discovery_id: str
    root_cause: str
    reasoning: str
    evidence_summary: List[str]
    confidence: int = Field(ge=0, le=100)
    business_impact: str
    recommended_action: str
    action_type: str
    investigation_mode: str  # "llm" | "fallback"

    @field_validator("confidence", mode="before")
    @classmethod
    def clamp_confidence(cls, v):
        try:
            return max(0, min(100, int(float(v))))
        except (TypeError, ValueError):
            return 50

    @field_validator("investigation_mode", mode="before")
    @classmethod
    def validate_mode(cls, v):
        return v if v in ("llm", "fallback") else "fallback"


# ── Gemini REST caller (same pattern as bargains.py) ───────────────────────

_GEMINI_URL_TEMPLATE = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-1.5-flash:generateContent?key={key}"
)

_CAUTIOUS_SYSTEM = (
    "You are a merchant analytics investigator. Your role is to explain WHY "
    "a statistical anomaly was detected in merchant payment/order data. "
    "IMPORTANT RULES: "
    "(1) Never claim definitive causation — use phrases like 'likely associated with', "
    "'evidence suggests', 'may be caused by', 'appears to correlate with'. "
    "(2) Return ONLY valid JSON matching the schema exactly. "
    "(3) Be concise and actionable."
)


def _build_prompt(discovery: dict) -> str:
    seg = ", ".join(f"{k}={v}" for k, v in discovery.get("segment", {}).items())
    evidence = "\n".join(f"  - {e}" for e in discovery.get("evidence", []))
    return (
        f"{_CAUTIOUS_SYSTEM}\n\n"
        f"A statistical ML pipeline (IsolationForest + Chi-Square subgroup analysis) "
        f"discovered the following pattern in merchant event data.\n\n"
        f"DISCOVERY:\n"
        f"  discovery_id   : {discovery.get('discovery_id')}\n"
        f"  problem_type   : {discovery.get('problem_type')}\n"
        f"  title          : {discovery.get('title')}\n"
        f"  segment        : {seg}\n"
        f"  severity       : {discovery.get('severity')}\n"
        f"  priority_score : {discovery.get('priority_score')}\n"
        f"  problem_rate   : {discovery.get('problem_rate', 0):.1%}\n"
        f"  baseline_rate  : {discovery.get('baseline_rate', 0):.1%}\n"
        f"  relative_change: {discovery.get('relative_change', 1):.2f}x\n"
        f"  affected_txns  : {discovery.get('affected_transactions')}\n"
        f"  revenue_at_risk: INR {discovery.get('estimated_revenue_at_risk', 0):,.0f}\n\n"
        f"STATISTICAL EVIDENCE:\n{evidence}\n\n"
        f"Your task: investigate this pattern and return a JSON object with EXACTLY these fields:\n"
        f"{{\n"
        f'  "root_cause": "<1-2 sentence likely root cause, using cautious language>",\n'
        f'  "reasoning": "<3-5 sentence investigation narrative explaining the pattern>",\n'
        f'  "evidence_summary": ["<point 1>", "<point 2>", "<point 3>"],\n'
        f'  "confidence": <integer 0-100>,\n'
        f'  "business_impact": "<1 sentence business impact statement>",\n'
        f'  "recommended_action": "<specific, actionable recommendation for the merchant>",\n'
        f'  "action_type": "<one of: payment_recovery, conversion_recovery, refund_review, bargainai_offer, monitor>"\n'
        f"}}\n"
        f"Return ONLY valid JSON. No markdown, no explanation."
    )


def _call_gemini(prompt: str, api_key: str) -> dict:
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.25,
            "responseMimeType": "application/json",
        },
    }
    url = _GEMINI_URL_TEMPLATE.format(key=api_key)
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        raw = data["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(raw)


# ── Deterministic fallback ─────────────────────────────────────────────────

_FALLBACK_TEMPLATES = {
    "PAYMENT_FAILURE": {
        "root_cause": (
            "Evidence suggests a payment gateway compatibility issue likely associated "
            "with specific device-payment method combinations, particularly during "
            "off-peak hours when gateway performance may degrade."
        ),
        "reasoning": (
            "The statistical pattern shows a significantly elevated failure rate in "
            "this segment compared to the global baseline. This type of cross-dimensional "
            "anomaly — combining device type, payment method, and time-of-day — is "
            "commonly associated with gateway routing mismatches or network instability. "
            "The high anomaly density detected by IsolationForest further corroborates "
            "that these transactions behave atypically."
        ),
        "evidence_summary": [
            "Failure rate in this segment substantially exceeds the global baseline",
            "High IsolationForest anomaly density suggests unusual transaction behavior",
            "Cross-dimensional pattern (device + payment + time) indicates gateway routing issue",
        ],
        "confidence": 72,
        "business_impact": (
            "Revenue recovery opportunity — a portion of failed transactions "
            "may be recoverable through alternative payment routing."
        ),
        "recommended_action": (
            "Enable alternate payment method suggestions for this device+method combination "
            "during late-night hours. Consider gateway health monitoring for this segment."
        ),
        "action_type": "payment_recovery",
    },
    "CHECKOUT_ABANDONMENT": {
        "root_cause": (
            "Evidence suggests price sensitivity or payment friction is likely associated "
            "with high cart abandonment in this segment, possibly due to a mismatch "
            "between product price expectations and available payment options."
        ),
        "reasoning": (
            "The abandonment rate in this segment is significantly above baseline. "
            "High-value product categories combined with certain payment methods "
            "may create friction at checkout — customers may hesitate when the total "
            "exceeds their comfort zone without flexible payment options. "
            "BargainAI's negotiation mechanism appears well-suited to recover "
            "these near-conversion customers."
        ),
        "evidence_summary": [
            "Abandonment rate in segment significantly exceeds global baseline",
            "Segment involves higher-value transactions where price sensitivity is elevated",
            "Pattern is statistically significant (chi-square p < 0.05)",
        ],
        "confidence": 68,
        "business_impact": (
            "Significant checkout recovery opportunity — a fraction of abandoned "
            "carts may convert with targeted intervention."
        ),
        "recommended_action": (
            "Launch a BargainAI offer campaign targeting this customer segment "
            "to provide a negotiation pathway and recover potential conversions."
        ),
        "action_type": "bargainai_offer",
    },
    "REFUND_SPIKE": {
        "root_cause": (
            "Evidence suggests a product quality, expectation mismatch, or "
            "category-specific issue is likely associated with the elevated refund "
            "rate in this segment."
        ),
        "reasoning": (
            "The refund rate significantly exceeds the global baseline for this segment. "
            "Category-specific refund spikes often indicate product quality issues, "
            "misleading product descriptions, or sizing/fit problems. "
            "Manual review is recommended before automated intervention to identify "
            "whether this is a systemic product issue or isolated incidents."
        ),
        "evidence_summary": [
            "Refund rate in this segment is materially above the global baseline",
            "Category-level pattern suggests a product or operational root cause",
            "Revenue fully at risk for refunded amounts",
        ],
        "confidence": 65,
        "business_impact": (
            "Direct revenue loss from refunds, plus reputational risk and "
            "operational cost of processing returns."
        ),
        "recommended_action": (
            "Initiate manual review of refund reasons for this product category. "
            "Check product descriptions, photos, and customer complaints for patterns."
        ),
        "action_type": "refund_review",
    },
    "LOW_CONVERSION": {
        "root_cause": (
            "Evidence suggests that customers in this segment are likely experiencing "
            "a barrier at checkout, possibly associated with price points, "
            "payment method availability, or trust signals."
        ),
        "reasoning": (
            "Low conversion in this segment — excluding already-abandoned or failed "
            "transactions — points to a friction point specific to this combination "
            "of attributes. The pattern may be associated with customers who browse "
            "but do not find sufficient incentive to complete the purchase. "
            "A targeted offer could provide the nudge needed to convert."
        ),
        "evidence_summary": [
            "Non-conversion rate in segment significantly exceeds baseline",
            "Pattern is statistically significant with sufficient sample size",
            "Revenue opportunity exists through targeted conversion recovery",
        ],
        "confidence": 60,
        "business_impact": (
            "Missed revenue from customers who entered the funnel but did not convert."
        ),
        "recommended_action": (
            "Test a BargainAI offer or limited-time discount for this customer "
            "segment to improve conversion rate."
        ),
        "action_type": "conversion_recovery",
    },
    "CUSTOMER_PRICE_SENSITIVITY": {
        "root_cause": (
            "Evidence suggests customers in this segment are highly price-sensitive, "
            "likely associated with product pricing exceeding the perceived value "
            "for this demographic or purchase context."
        ),
        "reasoning": (
            "High negotiation engagement in this segment indicates strong price "
            "sensitivity. The fact that the majority of successful negotiations "
            "convert after a discount suggests a price elasticity opportunity. "
            "BargainAI's negotiation framework is directly applicable here."
        ),
        "evidence_summary": [
            "Negotiation start rate well above baseline in this segment",
            "High conversion rate post-discount confirms price elasticity",
            "Systematic discount management can optimize margin vs. conversion",
        ],
        "confidence": 70,
        "business_impact": (
            "Current discount spend may be unoptimized; systematic management "
            "could improve both conversion rate and margin."
        ),
        "recommended_action": (
            "Deploy BargainAI campaign for this segment with a calibrated discount "
            "floor to systematically manage price-sensitive customers."
        ),
        "action_type": "bargainai_offer",
    },
}

_DEFAULT_FALLBACK = {
    "root_cause": (
        "Evidence suggests an unusual pattern in this segment that warrants further monitoring."
    ),
    "reasoning": (
        "The statistical analysis detected a significant deviation from baseline behaviour. "
        "Manual investigation is recommended to determine the root cause."
    ),
    "evidence_summary": [
        "Pattern rate exceeds baseline by at least 2x with statistical significance",
        "IsolationForest anomaly detection corroborates the pattern",
        "Further analysis required to identify specific root cause",
    ],
    "confidence": 50,
    "business_impact": "Business impact unclear; monitoring recommended.",
    "recommended_action": "Monitor this segment closely and investigate manually.",
    "action_type": "monitor",
}


def _deterministic_fallback(discovery: dict) -> dict:
    problem_type = discovery.get("problem_type", "")
    template = _FALLBACK_TEMPLATES.get(problem_type, _DEFAULT_FALLBACK)
    # Inject actual segment name into recommended_action for clarity
    seg_str = " & ".join(f"{v}" for v in discovery.get("segment", {}).values())
    result = dict(template)
    if seg_str:
        result["recommended_action"] = result["recommended_action"].rstrip(".") + (
            f" (Segment: {seg_str})."
        )
    return result


# ── Public interface ───────────────────────────────────────────────────────

def investigate(discovery: dict) -> InvestigationResult:
    """
    Main entry point. Accepts a Phase 2 discovery dict.
    Returns a validated InvestigationResult.
    """
    discovery_id = discovery.get("discovery_id", "unknown")
    api_key = os.getenv("AI_API_KEY", "").strip()

    llm_data = None
    mode = "fallback"

    if api_key:
        try:
            prompt = _build_prompt(discovery)
            raw = _call_gemini(prompt, api_key)

            # Validate required keys are present
            required = {
                "root_cause", "reasoning", "evidence_summary",
                "confidence", "business_impact", "recommended_action", "action_type"
            }
            if not required.issubset(raw.keys()):
                raise ValueError(f"LLM response missing keys: {required - raw.keys()}")

            llm_data = raw
            mode = "llm"
        except Exception:
            llm_data = None

    data = llm_data if llm_data is not None else _deterministic_fallback(discovery)

    return InvestigationResult(
        discovery_id=discovery_id,
        root_cause=str(data.get("root_cause", "")),
        reasoning=str(data.get("reasoning", "")),
        evidence_summary=list(data.get("evidence_summary", [])),
        confidence=data.get("confidence", 50),
        business_impact=str(data.get("business_impact", "")),
        recommended_action=str(data.get("recommended_action", "")),
        action_type=str(data.get("action_type", "monitor")),
        investigation_mode=mode,
    )
