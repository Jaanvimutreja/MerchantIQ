"""
backend/tests/test_resolution.py

Phase 4 tests — closed-loop resolution pipeline:

  - Resolution engine produces valid output
  - 3 different discoveries → 3 different action types / outcomes
  - Outcome schema is correct (recovery_rate, action_success, etc.)
  - Safety: refund_review is never auto-executed (pending_approval)
  - Feedback metrics are computed and non-negative
  - DB persistence via in-memory SQLite
"""
import os
import sys
import pytest
from datetime import datetime

# Ensure backend/ is on path so ai.* module registrations are consistent
_backend = os.path.join(os.path.dirname(__file__), "..")
_backend = os.path.abspath(_backend)
if _backend not in sys.path:
    sys.path.insert(0, _backend)

# Use an in-memory SQLite DB for tests — avoids touching production bargainai2.db
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base

# Import Resolution model so it gets registered with Base before create_all
import ai.outcome_tracker  # noqa: F401

from ai.outcome_tracker import (
    Resolution, estimate_outcome, save_resolution,
    get_resolution, list_resolutions, resolution_to_dict,
    compute_feedback,
)
from ai.resolution_engine import ResolutionEngine
from ai.investigator import investigate
from ai.decision_engine import decide
from ai.action_executor import execute


# ── Test DB setup ──────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def db_session():
    """Provide an in-memory SQLite session for tests."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


# ── Sample discoveries ─────────────────────────────────────────────────────

PAYMENT_DISC = {
    "discovery_id": "DISC-P4-001",
    "problem_type": "PAYMENT_FAILURE",
    "title": "Payment Failure in Android + Debit Card + Late Night",
    "segment": {"device_type": "Android", "payment_method": "Debit Card", "is_late_night": "1"},
    "severity": "HIGH",
    "priority_score": 60.0,
    "affected_transactions": 34,
    "problem_rate": 0.453,
    "baseline_rate": 0.065,
    "relative_change": 6.97,
    "estimated_revenue_at_risk": 103666.0,
    "evidence": ["Failure rate 45.3% vs 6.5% baseline", "6.97x relative change"],
    "detection_method": ["IsolationForest", "Chi-Square"],
}

REFUND_DISC = {
    "discovery_id": "DISC-P4-002",
    "problem_type": "REFUND_SPIKE",
    "title": "Refund Spike in Fashion & Apparel",
    "segment": {"product_category": "Fashion & Apparel"},
    "severity": "MEDIUM",
    "priority_score": 44.5,
    "affected_transactions": 242,
    "problem_rate": 0.147,
    "baseline_rate": 0.052,
    "relative_change": 2.84,
    "estimated_revenue_at_risk": 654429.0,
    "evidence": ["Refund rate 14.7% vs 5.2% baseline", "2.84x relative change"],
    "detection_method": ["IsolationForest", "Chi-Square"],
}

CHECKOUT_DISC = {
    "discovery_id": "DISC-P4-003",
    "problem_type": "CHECKOUT_ABANDONMENT",
    "title": "Checkout Abandonment in Luxury + Credit Card",
    "segment": {"product_category": "Luxury & Watches", "payment_method": "Credit Card"},
    "severity": "MEDIUM",
    "priority_score": 52.3,
    "affected_transactions": 140,
    "problem_rate": 0.438,
    "baseline_rate": 0.105,
    "relative_change": 4.17,
    "estimated_revenue_at_risk": 930515.0,
    "evidence": ["Abandonment rate 43.8% vs 10.5% baseline", "4.17x relative change"],
    "detection_method": ["IsolationForest", "Chi-Square"],
}

LOW_CONV_DISC = {
    "discovery_id": "DISC-P4-004",
    "problem_type": "LOW_CONVERSION",
    "title": "Low Conversion in iOS + UPI + 2K-5K",
    "segment": {"device_type": "iOS", "payment_method": "UPI", "amount_bucket": "2K-5K"},
    "severity": "MEDIUM",
    "priority_score": 36.1,
    "affected_transactions": 51,
    "problem_rate": 0.097,
    "baseline_rate": 0.046,
    "relative_change": 2.13,
    "estimated_revenue_at_risk": 47457.0,
    "evidence": ["Non-conversion rate 9.7% vs 4.6% baseline"],
    "detection_method": ["IsolationForest", "Chi-Square"],
}


# ── Resolution engine tests ────────────────────────────────────────────────

def test_resolution_engine_returns_full_pipeline(db_session):
    """ResolutionEngine.resolve() must return all pipeline stages."""
    original = os.environ.pop("AI_API_KEY", None)
    try:
        engine = ResolutionEngine()
        result = engine.resolve(PAYMENT_DISC, db_session)

        assert "discovery" in result
        assert "investigation" in result
        assert "decision" in result
        assert "execution" in result
        assert "resolution" in result
    finally:
        if original is not None:
            os.environ["AI_API_KEY"] = original


def test_three_discoveries_produce_different_action_types(db_session):
    """Three different problem_types must resolve to three different action_types."""
    original = os.environ.pop("AI_API_KEY", None)
    try:
        engine = ResolutionEngine()
        r1 = engine.resolve(PAYMENT_DISC, db_session)
        r2 = engine.resolve(REFUND_DISC, db_session)
        r3 = engine.resolve(CHECKOUT_DISC, db_session)

        a1 = r1["resolution"]["action_type"]
        a2 = r2["resolution"]["action_type"]
        a3 = r3["resolution"]["action_type"]

        # All three should differ
        assert a1 != a2 or a1 != a3, (
            f"Expected different action types, got: {a1}, {a2}, {a3}"
        )

        # Specific expectations
        assert a1 == "payment_recovery"
        assert a2 == "refund_review"
        assert a3 == "bargainai_offer"
    finally:
        if original is not None:
            os.environ["AI_API_KEY"] = original


def test_refund_spike_is_never_auto_executed(db_session):
    """REFUND_SPIKE must have status=pending_approval and automation_allowed=False."""
    original = os.environ.pop("AI_API_KEY", None)
    try:
        engine = ResolutionEngine()
        result = engine.resolve(REFUND_DISC, db_session)

        exec_status = result["execution"]["status"]
        auto = result["decision"]["automation_allowed"]

        assert exec_status == "pending_approval", (
            f"Expected pending_approval for refund_review, got: {exec_status}"
        )
        assert auto is False
    finally:
        if original is not None:
            os.environ["AI_API_KEY"] = original


# ── Outcome schema tests ───────────────────────────────────────────────────

def test_outcome_schema_is_correct(db_session):
    """Resolution row must have correct schema and non-negative numeric fields."""
    original = os.environ.pop("AI_API_KEY", None)
    try:
        engine = ResolutionEngine()
        result = engine.resolve(LOW_CONV_DISC, db_session)
        res = result["resolution"]

        assert res["resolution_id"].startswith("RES-")
        assert res["discovery_id"] == "DISC-P4-004"
        assert res["status"] in ("success", "failed", "pending", "pending_approval", "blocked")
        assert res["recovered_amount"] >= 0
        assert res["revenue_at_risk"] >= 0
        assert res["customers_affected"] >= 0
        assert 0.0 <= res["recovery_rate"] <= 1.0
        assert isinstance(res["action_success"], bool)
        assert res["message"]
        assert res["created_at"] is not None
    finally:
        if original is not None:
            os.environ["AI_API_KEY"] = original


def test_feedback_metrics_are_non_negative(db_session):
    """Feedback block in resolution must have non-negative values."""
    original = os.environ.pop("AI_API_KEY", None)
    try:
        engine = ResolutionEngine()
        result = engine.resolve(PAYMENT_DISC, db_session)
        feedback = result["resolution"]["feedback"]

        assert feedback["revenue_at_risk"] >= 0
        assert feedback["revenue_recovered"] >= 0
        assert 0.0 <= feedback["recovery_rate"] <= 1.0
        assert isinstance(feedback["action_success"], bool)
        assert feedback["customers_affected"] >= 0
    finally:
        if original is not None:
            os.environ["AI_API_KEY"] = original


# ── DB persistence tests ───────────────────────────────────────────────────

def test_resolutions_are_persisted_in_db(db_session):
    """All resolved discoveries must be retrievable from DB."""
    original = os.environ.pop("AI_API_KEY", None)
    try:
        engine = ResolutionEngine()
        r = engine.resolve(PAYMENT_DISC, db_session)
        res_id = r["resolution"]["resolution_id"]

        # Must be retrievable
        row = get_resolution(db_session, res_id)
        assert row is not None
        assert row.resolution_id == res_id
        assert row.discovery_id == "DISC-P4-001"
    finally:
        if original is not None:
            os.environ["AI_API_KEY"] = original


def test_list_resolutions_returns_all_stored(db_session):
    """list_resolutions() must return at least the rows we persisted."""
    rows = list_resolutions(db_session)
    assert len(rows) >= 1
    for row in rows:
        d = resolution_to_dict(row)
        assert d["resolution_id"]
        assert d["recovery_rate"] >= 0
        assert d["feedback"]["action_success"] in (True, False)


# ── Recovery rate sanity tests ─────────────────────────────────────────────

def test_payment_recovery_recovers_some_revenue(db_session):
    """payment_recovery action must recover > 0 INR (sim rate 35%)."""
    original = os.environ.pop("AI_API_KEY", None)
    try:
        engine = ResolutionEngine()
        result = engine.resolve(PAYMENT_DISC, db_session)
        recovered = result["resolution"]["recovered_amount"]
        # PAYMENT_DISC has revenue_at_risk=103666 → 35% = ~36283
        assert recovered > 0, "payment_recovery should recover some revenue"
        assert recovered < PAYMENT_DISC["estimated_revenue_at_risk"]
    finally:
        if original is not None:
            os.environ["AI_API_KEY"] = original


def test_refund_review_has_lower_recovery_than_payment_recovery(db_session):
    """refund_review (15% sim rate) should recover less than payment_recovery (35%)."""
    original = os.environ.pop("AI_API_KEY", None)
    try:
        engine = ResolutionEngine()
        # Use same revenue_at_risk for fair comparison
        disc_pay = dict(PAYMENT_DISC, estimated_revenue_at_risk=100000, discovery_id="DISC-P4-CMP1")
        disc_ref = dict(REFUND_DISC, estimated_revenue_at_risk=100000, discovery_id="DISC-P4-CMP2")
        r_pay = engine.resolve(disc_pay, db_session)
        r_ref = engine.resolve(disc_ref, db_session)

        assert (
            r_pay["resolution"]["recovered_amount"]
            > r_ref["resolution"]["recovered_amount"]
        ), "payment_recovery should recover more than refund_review"
    finally:
        if original is not None:
            os.environ["AI_API_KEY"] = original
