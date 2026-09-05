"""
backend/ai/outcome_tracker.py

Tracks resolution outcomes and computes feedback metrics.

Schema for Resolution (stored in SQLite via SQLAlchemy):
  resolution_id     : unique string (RES-<timestamp>-<discovery_id>)
  discovery_id      : Phase 2 discovery ID
  action_type       : which action was executed
  status            : "success" | "failed" | "pending"
  recovered_amount  : float (INR, estimated recovery)
  customers_affected: int
  message           : human-readable outcome description
  created_at        : naive UTC datetime

Feedback schema (computed, not persisted separately):
  recovery_rate     : recovered_amount / estimated_revenue_at_risk  (0-1)
  revenue_recovered : recovered_amount
  action_success    : bool (status == "success")
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import Session

from database import Base


# ── SQLAlchemy model ──────────────────────────────────────────────────────

def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Resolution(Base):
    __tablename__ = "resolutions"
    __table_args__ = {"extend_existing": True}

    id              = Column(Integer, primary_key=True, index=True)
    resolution_id   = Column(String, unique=True, nullable=False, index=True)
    discovery_id    = Column(String, nullable=False, index=True)
    problem_type    = Column(String, nullable=True)
    action_type     = Column(String, nullable=False)
    status          = Column(String, nullable=False, default="pending")   # success|failed|pending
    recovered_amount    = Column(Float, nullable=False, default=0.0)
    revenue_at_risk     = Column(Float, nullable=False, default=0.0)
    customers_affected  = Column(Integer, nullable=False, default=0)
    recovery_rate       = Column(Float, nullable=False, default=0.0)
    action_success      = Column(Integer, nullable=False, default=0)      # 0/1 (SQLite has no bool)
    message         = Column(Text, nullable=True)
    # JSON-serialised snapshot of investigation + decision for auditability
    investigation_summary = Column(Text, nullable=True)
    created_at      = Column(DateTime, default=_utcnow)


# ── Recovery estimation helpers ───────────────────────────────────────────
# These are SIMULATION estimates — not real payment data.
# Assumptions are documented here and in README.

_RECOVERY_RATE_BY_ACTION: dict[str, float] = {
    # payment_recovery: surfacing alternate methods may convert ~35% of failed txns
    "payment_recovery":    0.35,
    # bargainai_offer: negotiation campaigns historically convert ~40% of abandoners
    "bargainai_offer":     0.40,
    # conversion_recovery: nudge converts ~20% of non-converting segment
    "conversion_recovery": 0.20,
    # refund_review: manual review may prevent ~15% of future refunds
    "refund_review":       0.15,
    # follow_up: generic follow-up converts ~10%
    "follow_up":           0.10,
    # monitor: no direct recovery
    "monitor":             0.00,
}

# Customers affected: fraction of affected_transactions per action type
_CUSTOMERS_FRACTION_BY_ACTION: dict[str, float] = {
    "payment_recovery":    1.00,   # all failed txns targeted
    "bargainai_offer":     0.80,   # 80% of abandonments reached
    "conversion_recovery": 0.60,
    "refund_review":       0.30,   # only escalated refunds reviewed
    "follow_up":           0.50,
    "monitor":             0.00,
}


def estimate_outcome(
    discovery: dict,
    decision,          # ActionDecision Pydantic model
    execution: dict,
) -> dict:
    """
    Simulate what an outcome WOULD look like if the action were taken.
    Returns a dict ready to be persisted as a Resolution row.

    IMPORTANT: This is a DRY-RUN estimate, not real money recovered.
    """
    action_type = decision.action_type
    revenue_at_risk = float(discovery.get("estimated_revenue_at_risk", 0.0))
    affected_txns = int(discovery.get("affected_transactions", 0))

    # Simulated recovery based on documented rate assumptions
    sim_rate = _RECOVERY_RATE_BY_ACTION.get(action_type, 0.0)
    recovered = round(revenue_at_risk * sim_rate, 2)

    cust_frac = _CUSTOMERS_FRACTION_BY_ACTION.get(action_type, 0.0)
    customers_affected = max(1, int(affected_txns * cust_frac)) if affected_txns > 0 else 0

    # Determine status: monitor/refund_review remain "pending" (need human); others succeed
    if action_type in ("monitor", "refund_review"):
        status = "pending"
        success = False
    elif execution.get("status") == "simulated":
        status = "success"
        success = True
    else:
        status = "failed"
        success = False

    recovery_rate = round(recovered / revenue_at_risk, 4) if revenue_at_risk > 0 else 0.0

    res_id = f"RES-{discovery['discovery_id']}-{uuid.uuid4().hex[:8].upper()}"

    message = _build_message(action_type, recovered, customers_affected, status, recovery_rate)

    return {
        "resolution_id":       res_id,
        "discovery_id":        discovery["discovery_id"],
        "problem_type":        discovery.get("problem_type", ""),
        "action_type":         action_type,
        "status":              status,
        "recovered_amount":    recovered,
        "revenue_at_risk":     revenue_at_risk,
        "customers_affected":  customers_affected,
        "recovery_rate":       recovery_rate,
        "action_success":      1 if success else 0,
        "message":             message,
    }


def _build_message(
    action_type: str,
    recovered: float,
    customers: int,
    status: str,
    rate: float,
) -> str:
    base = {
        "payment_recovery": (
            f"[SIMULATED] Alternate payment method surfaced to {customers} customers. "
            f"Estimated recovery: INR {recovered:,.0f} ({rate:.0%} of revenue at risk)."
        ),
        "bargainai_offer": (
            f"[SIMULATED] BargainAI negotiation campaign launched for {customers} customers. "
            f"Estimated recovery: INR {recovered:,.0f} ({rate:.0%} of revenue at risk)."
        ),
        "conversion_recovery": (
            f"[SIMULATED] Conversion nudge sent to {customers} customers. "
            f"Estimated recovery: INR {recovered:,.0f} ({rate:.0%} of revenue at risk)."
        ),
        "refund_review": (
            f"[SIMULATED] {customers} transactions flagged for manual review. "
            f"Estimated preventable refund exposure: INR {recovered:,.0f}. "
            f"Status: pending merchant review."
        ),
        "follow_up": (
            f"[SIMULATED] Follow-up triggered for {customers} customers. "
            f"Estimated recovery: INR {recovered:,.0f}."
        ),
        "monitor": (
            f"[SIMULATED] Segment added to watchlist. "
            f"No direct revenue action taken — monitoring for trend changes."
        ),
    }
    return base.get(action_type, f"[SIMULATED] Action completed. Status: {status}.")


# ── Feedback computation ──────────────────────────────────────────────────

def compute_feedback(resolution_row: Resolution) -> dict:
    """
    Compute feedback metrics from a stored resolution.
    These metrics inform future decision quality.
    """
    return {
        "resolution_id":    resolution_row.resolution_id,
        "discovery_id":     resolution_row.discovery_id,
        "action_type":      resolution_row.action_type,
        "revenue_at_risk":  resolution_row.revenue_at_risk,
        "revenue_recovered": resolution_row.recovered_amount,
        "recovery_rate":    resolution_row.recovery_rate,
        "action_success":   bool(resolution_row.action_success),
        "customers_affected": resolution_row.customers_affected,
        "status":           resolution_row.status,
        # Comparative signal for future priority decisions
        "impact_delta":     round(
            resolution_row.recovered_amount - resolution_row.revenue_at_risk, 2
        ),
        "created_at":       resolution_row.created_at.isoformat()
                            if resolution_row.created_at else None,
    }


# ── DB persistence helpers ────────────────────────────────────────────────

def save_resolution(db: Session, outcome: dict, investigation_summary: str = "") -> Resolution:
    """Persist an outcome dict as a Resolution row."""
    row = Resolution(
        resolution_id       = outcome["resolution_id"],
        discovery_id        = outcome["discovery_id"],
        problem_type        = outcome.get("problem_type", ""),
        action_type         = outcome["action_type"],
        status              = outcome["status"],
        recovered_amount    = outcome["recovered_amount"],
        revenue_at_risk     = outcome["revenue_at_risk"],
        customers_affected  = outcome["customers_affected"],
        recovery_rate       = outcome["recovery_rate"],
        action_success      = outcome["action_success"],
        message             = outcome["message"],
        investigation_summary = investigation_summary,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_resolution(db: Session, resolution_id: str) -> Optional[Resolution]:
    return db.query(Resolution).filter(
        Resolution.resolution_id == resolution_id
    ).first()


def list_resolutions(db: Session) -> list[Resolution]:
    return db.query(Resolution).order_by(Resolution.created_at.desc()).all()


def resolution_to_dict(row: Resolution) -> dict:
    return {
        "resolution_id":      row.resolution_id,
        "discovery_id":       row.discovery_id,
        "problem_type":       row.problem_type,
        "action_type":        row.action_type,
        "status":             row.status,
        "recovered_amount":   row.recovered_amount,
        "revenue_at_risk":    row.revenue_at_risk,
        "customers_affected": row.customers_affected,
        "recovery_rate":      row.recovery_rate,
        "action_success":     bool(row.action_success),
        "message":            row.message,
        "created_at":         row.created_at.isoformat() if row.created_at else None,
        "feedback":           compute_feedback(row),
    }
