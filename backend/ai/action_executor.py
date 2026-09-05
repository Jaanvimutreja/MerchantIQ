"""
backend/ai/action_executor.py

Safe DRY-RUN executor.

This module simulates what the action WOULD do in production.
No real system mutations occur: no database writes, no payment calls,
no API calls to Razorpay or any external service.

Every execution returns status="simulated" so it is unambiguous
that nothing real happened.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


# ── Simulation messages per action_type ────────────────────────────────────

_SIMULATION_MESSAGES: dict[str, str] = {
    "payment_recovery": (
        "[DRY-RUN] Would surface alternate payment method options (UPI, Wallet) "
        "to affected customers. Gateway health alert would be raised for monitoring."
    ),
    "bargainai_offer": (
        "[DRY-RUN] Would create a BargainAI negotiation campaign targeting this "
        "customer segment with merchant-configured discount bounds."
    ),
    "conversion_recovery": (
        "[DRY-RUN] Would send a limited-time BargainAI invite or discount nudge "
        "to customers in this segment who viewed but did not purchase."
    ),
    "refund_review": (
        "[DRY-RUN] Would compile refund reason breakdown for this segment and "
        "surface it to the merchant dashboard for manual review. "
        "No automated refund is issued."
    ),
    "monitor": (
        "[DRY-RUN] Would add this segment to the monitoring watchlist and "
        "schedule a re-run of the discovery pipeline in 24 hours."
    ),
}

_DEFAULT_MESSAGE = (
    "[DRY-RUN] Would trigger the specified action for this segment. "
    "No real system change has occurred."
)


def execute(action_decision: Any) -> dict:
    """
    Simulate execution of an ActionDecision.

    Parameters
    ----------
    action_decision : ActionDecision (or any object with action_type and action attrs)

    Returns
    -------
    dict with status="simulated", action_type, message, and timestamp.
    """
    action_type = getattr(action_decision, "action_type", "monitor")
    automation_allowed = getattr(action_decision, "automation_allowed", False)
    risk_level = getattr(action_decision, "risk_level", "LOW")

    message = _SIMULATION_MESSAGES.get(action_type, _DEFAULT_MESSAGE)

    # Add automation eligibility context to message
    if not automation_allowed:
        message += (
            f" NOTE: automation_allowed=False (risk_level={risk_level}). "
            "This action requires explicit merchant approval before execution."
        )
    else:
        message += " This action is eligible for automated execution when approved."

    return {
        "status": "simulated",
        "action_type": action_type,
        "message": message,
        "automation_allowed": automation_allowed,
        "risk_level": risk_level,
        "simulated_at": datetime.now(timezone.utc).isoformat(),
    }
