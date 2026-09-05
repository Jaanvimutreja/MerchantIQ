"""
backend/ai/decision_engine.py

Deterministic rule engine that converts an InvestigationResult into
a safe, bounded action decision.

SAFETY RULES (hard-coded, never bypassed by LLM):
- Only LOW-risk actions may have automation_allowed=True.
- Refunds, money transfers, order cancellations are always HIGH-risk
  and automation_allowed=False.
- The LLM can suggest; this engine decides.
"""
from __future__ import annotations

from typing import Literal
from pydantic import BaseModel


# ── Pydantic output schema ─────────────────────────────────────────────────

RiskLevel = Literal["LOW", "MEDIUM", "HIGH"]


class ActionDecision(BaseModel):
    action_type: str
    action: str
    reason: str
    automation_allowed: bool
    risk_level: RiskLevel


# ── Action type catalogue ──────────────────────────────────────────────────
# Each entry: (action_type, action_description, risk_level, automation_allowed)
# automation_allowed is ONLY True when risk_level == "LOW"

_ACTION_CATALOGUE: dict[str, tuple[str, str, RiskLevel, bool]] = {
    # ── Payment recovery ───────────────────────────────────────────────────
    "payment_recovery": (
        "payment_recovery",
        (
            "Surface alternate payment method suggestions (UPI, Wallet) to customers "
            "encountering failures in this segment. Flag segment for gateway health monitoring."
        ),
        "LOW",
        True,   # Safe: surfacing suggestions, no financial action
    ),
    # ── BargainAI offer ────────────────────────────────────────────────────
    "bargainai_offer": (
        "bargainai_offer",
        (
            "Create a targeted BargainAI negotiation campaign for this customer segment "
            "with a merchant-configured discount floor. Customers can negotiate within bounds."
        ),
        "LOW",
        True,   # Safe: initiates a negotiation campaign, merchant controls bounds
    ),
    # ── Conversion recovery ────────────────────────────────────────────────
    "conversion_recovery": (
        "conversion_recovery",
        (
            "Send a limited-time discount nudge or BargainAI invite to customers "
            "in this segment who have viewed but not purchased."
        ),
        "LOW",
        True,   # Safe: marketing nudge only
    ),
    # ── Refund review ──────────────────────────────────────────────────────
    "refund_review": (
        "refund_review",
        (
            "Flag this segment for manual merchant review. Compile refund reason "
            "breakdown and surface to merchant dashboard. No automated refund issuance."
        ),
        "MEDIUM",
        False,  # Requires human review before action
    ),
    # ── Monitor ───────────────────────────────────────────────────────────
    "monitor": (
        "monitor",
        (
            "Add this segment to the monitoring watchlist. "
            "Re-run discovery pipeline in 24 hours to track trend."
        ),
        "LOW",
        True,   # Safe: read-only monitoring
    ),
    # ── Safety guardrail: financial actions are NEVER automated ───────────
    "issue_refund": (
        "refund_review",  # Redirect to review instead
        (
            "BLOCKED: Automated refund issuance is not permitted. "
            "Redirected to manual review flow."
        ),
        "HIGH",
        False,
    ),
    "cancel_order": (
        "monitor",
        (
            "BLOCKED: Automated order cancellation is not permitted. "
            "Flagged for manual review."
        ),
        "HIGH",
        False,
    ),
    "transfer_money": (
        "monitor",
        "BLOCKED: Automated money transfer is not permitted.",
        "HIGH",
        False,
    ),
}

# Map ML problem_type → preferred action_type (LLM can override if valid)
_PROBLEM_TYPE_DEFAULTS: dict[str, str] = {
    "PAYMENT_FAILURE": "payment_recovery",
    "CHECKOUT_ABANDONMENT": "bargainai_offer",
    "REFUND_SPIKE": "refund_review",
    "LOW_CONVERSION": "conversion_recovery",
    "CUSTOMER_PRICE_SENSITIVITY": "bargainai_offer",
    "OTHER_ANOMALY": "monitor",
}

# Valid action_type values that the LLM may suggest
_SAFE_LLM_ACTION_TYPES = {
    "payment_recovery", "bargainai_offer", "conversion_recovery",
    "refund_review", "monitor",
}


def decide(investigation, discovery: dict) -> ActionDecision:
    """
    Convert an InvestigationResult + original discovery into an ActionDecision.

    Priority:
    1. Use the action_type from the investigator (LLM or fallback) if it is
       in the safe catalogue.
    2. Otherwise fall back to the problem_type default.
    3. Always apply hard safety guardrails.
    """
    problem_type = discovery.get("problem_type", "OTHER_ANOMALY")
    llm_action_type = getattr(investigation, "action_type", "monitor")

    # Resolve action type: prefer LLM suggestion if it is a safe option
    if llm_action_type in _SAFE_LLM_ACTION_TYPES:
        chosen = llm_action_type
    else:
        # Hard guardrail: block unsafe LLM suggestions
        chosen = _PROBLEM_TYPE_DEFAULTS.get(problem_type, "monitor")

    # Extra guardrail: financial/irreversible actions are never automated
    if chosen in ("issue_refund", "cancel_order", "transfer_money"):
        chosen = "refund_review"

    entry = _ACTION_CATALOGUE.get(chosen, _ACTION_CATALOGUE["monitor"])
    action_type_out, action, risk_level, automation_allowed = entry

    # Safety invariant: automation_allowed ONLY if risk is LOW
    if risk_level != "LOW":
        automation_allowed = False

    reason = (
        f"ML detected {problem_type.replace('_', ' ').lower()} "
        f"(priority={discovery.get('priority_score', 0)}, "
        f"relative change={discovery.get('relative_change', 1):.1f}x). "
        f"Investigator confidence: {getattr(investigation, 'confidence', 0)}%. "
        f"Action selected: {chosen}."
    )

    return ActionDecision(
        action_type=action_type_out,
        action=action,
        reason=reason,
        automation_allowed=automation_allowed,
        risk_level=risk_level,
    )
