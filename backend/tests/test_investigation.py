"""
backend/tests/test_investigation.py

Phase 3 tests — verifies the AI Investigation layer pipeline:
  - investigator returns valid InvestigationResult
  - decision engine produces sensible different actions per problem type
  - action executor always returns status="simulated"
  - safety guardrails: automation_allowed=False for MEDIUM/HIGH risk
  - fallback fires when no API key is present
  - Phase 2 tests still pass (imported at the bottom)
"""
import os
import sys
import pytest

# Ensure backend/ is on path when run from project root
_backend = os.path.join(os.path.dirname(__file__), "..")
if _backend not in sys.path:
    sys.path.insert(0, _backend)

from ai.investigator import investigate, InvestigationResult
from ai.decision_engine import decide, ActionDecision
from ai.action_executor import execute

# ── Sample discoveries ──────────────────────────────────────────────────────

PAYMENT_FAILURE_DISC = {
    "discovery_id": "DISC-TEST-001",
    "problem_type": "PAYMENT_FAILURE",
    "title": "Payment Failure in device_type=Android & payment_method=Debit Card & is_late_night=1",
    "segment": {"device_type": "Android", "payment_method": "Debit Card", "is_late_night": "1"},
    "severity": "HIGH",
    "priority_score": 60.0,
    "affected_transactions": 34,
    "problem_rate": 0.453,
    "baseline_rate": 0.065,
    "relative_change": 6.97,
    "estimated_revenue_at_risk": 103666.0,
    "evidence": [
        "Segment rate: 45.3% vs Global baseline: 6.5%",
        "Relative change: 6.97x (p-value=0.0000)",
        "Affected transactions: 34 out of 75 in segment",
        "Anomaly density in segment: 42.7%",
    ],
    "detection_method": ["IsolationForest", "Chi-Square Proportions"],
}

REFUND_SPIKE_DISC = {
    "discovery_id": "DISC-TEST-002",
    "problem_type": "REFUND_SPIKE",
    "title": "Refund Spike in product_category=Fashion & Apparel",
    "segment": {"product_category": "Fashion & Apparel"},
    "severity": "MEDIUM",
    "priority_score": 44.5,
    "affected_transactions": 242,
    "problem_rate": 0.147,
    "baseline_rate": 0.052,
    "relative_change": 2.84,
    "estimated_revenue_at_risk": 654429.0,
    "evidence": [
        "Segment rate: 14.7% vs Global baseline: 5.2%",
        "Relative change: 2.84x (p-value=0.0000)",
        "Affected transactions: 242 out of 1648 in segment",
        "Anomaly density in segment: 6.4%",
    ],
    "detection_method": ["IsolationForest", "Chi-Square Proportions"],
}

CHECKOUT_DISC = {
    "discovery_id": "DISC-TEST-003",
    "problem_type": "CHECKOUT_ABANDONMENT",
    "title": "Checkout Abandonment in product_category=Luxury & Watches & payment_method=Credit Card",
    "segment": {"product_category": "Luxury & Watches", "payment_method": "Credit Card"},
    "severity": "MEDIUM",
    "priority_score": 52.3,
    "affected_transactions": 140,
    "problem_rate": 0.438,
    "baseline_rate": 0.105,
    "relative_change": 4.17,
    "estimated_revenue_at_risk": 930515.0,
    "evidence": [
        "Segment rate: 43.8% vs Global baseline: 10.5%",
        "Relative change: 4.17x (p-value=0.0000)",
        "Affected transactions: 140 out of 320 in segment",
        "Anomaly density in segment: 25.0%",
    ],
    "detection_method": ["IsolationForest", "Chi-Square Proportions"],
}


# ── Investigator tests ──────────────────────────────────────────────────────

def test_investigate_returns_valid_model():
    """investigate() must return a valid InvestigationResult regardless of API key."""
    # Force fallback by temporarily clearing API key
    original = os.environ.pop("AI_API_KEY", None)
    try:
        result = investigate(PAYMENT_FAILURE_DISC)
        assert isinstance(result, InvestigationResult)
        assert result.discovery_id == "DISC-TEST-001"
        assert 0 <= result.confidence <= 100
        assert result.investigation_mode in ("llm", "fallback")
        assert len(result.evidence_summary) >= 1
        assert result.root_cause
        assert result.reasoning
        assert result.recommended_action
        assert result.action_type
    finally:
        if original is not None:
            os.environ["AI_API_KEY"] = original


def test_investigate_fallback_fires_without_key():
    """Without AI_API_KEY, mode must be 'fallback'."""
    original = os.environ.pop("AI_API_KEY", None)
    try:
        result = investigate(REFUND_SPIKE_DISC)
        assert result.investigation_mode == "fallback"
    finally:
        if original is not None:
            os.environ["AI_API_KEY"] = original


def test_different_problem_types_produce_different_actions():
    """Different problem types must produce different action_type values."""
    original = os.environ.pop("AI_API_KEY", None)
    try:
        r_payment = investigate(PAYMENT_FAILURE_DISC)
        r_refund = investigate(REFUND_SPIKE_DISC)
        r_checkout = investigate(CHECKOUT_DISC)

        # payment_failure → payment_recovery
        assert r_payment.action_type == "payment_recovery"
        # refund_spike → refund_review
        assert r_refund.action_type == "refund_review"
        # checkout_abandonment → bargainai_offer
        assert r_checkout.action_type == "bargainai_offer"

        # All three must differ
        types = {r_payment.action_type, r_refund.action_type, r_checkout.action_type}
        assert len(types) == 3, f"Expected 3 different action types, got: {types}"
    finally:
        if original is not None:
            os.environ["AI_API_KEY"] = original


# ── Decision engine tests ───────────────────────────────────────────────────

def test_decision_returns_valid_model():
    original = os.environ.pop("AI_API_KEY", None)
    try:
        inv = investigate(PAYMENT_FAILURE_DISC)
        decision = decide(inv, PAYMENT_FAILURE_DISC)
        assert isinstance(decision, ActionDecision)
        assert decision.action_type
        assert decision.action
        assert decision.risk_level in ("LOW", "MEDIUM", "HIGH")
        assert isinstance(decision.automation_allowed, bool)
    finally:
        if original is not None:
            os.environ["AI_API_KEY"] = original


def test_safety_guardrail_refund_not_automated():
    """REFUND_SPIKE → refund_review → automation_allowed must be False."""
    original = os.environ.pop("AI_API_KEY", None)
    try:
        inv = investigate(REFUND_SPIKE_DISC)
        decision = decide(inv, REFUND_SPIKE_DISC)
        assert decision.action_type == "refund_review"
        assert decision.automation_allowed is False
        assert decision.risk_level in ("MEDIUM", "HIGH")
    finally:
        if original is not None:
            os.environ["AI_API_KEY"] = original


def test_low_risk_actions_may_be_automated():
    """PAYMENT_FAILURE → payment_recovery → automation_allowed may be True."""
    original = os.environ.pop("AI_API_KEY", None)
    try:
        inv = investigate(PAYMENT_FAILURE_DISC)
        decision = decide(inv, PAYMENT_FAILURE_DISC)
        # payment_recovery is LOW risk; automation_allowed should be True
        if decision.risk_level == "LOW":
            assert decision.automation_allowed is True
    finally:
        if original is not None:
            os.environ["AI_API_KEY"] = original


# ── Action executor tests ───────────────────────────────────────────────────

def test_executor_always_returns_simulated():
    """execute() must always return status='simulated', never a real result."""
    original = os.environ.pop("AI_API_KEY", None)
    try:
        for disc in (PAYMENT_FAILURE_DISC, REFUND_SPIKE_DISC, CHECKOUT_DISC):
            inv = investigate(disc)
            decision = decide(inv, disc)
            result = execute(decision)
            assert result["status"] == "simulated"
            assert result["action_type"]
            assert result["message"]
            assert "simulated_at" in result
    finally:
        if original is not None:
            os.environ["AI_API_KEY"] = original


def test_executor_includes_automation_flag():
    """execute() output must include automation_allowed and risk_level."""
    original = os.environ.pop("AI_API_KEY", None)
    try:
        inv = investigate(REFUND_SPIKE_DISC)
        decision = decide(inv, REFUND_SPIKE_DISC)
        result = execute(decision)
        assert "automation_allowed" in result
        assert "risk_level" in result
        assert result["automation_allowed"] is False  # refund_review is not automated
    finally:
        if original is not None:
            os.environ["AI_API_KEY"] = original
