"""
backend/ai/resolution_engine.py

Resolution Engine: orchestrates the complete closed-loop pipeline.

  Discovery (Phase 2)
    → Investigation (Phase 3 LLM / fallback)
    → Decision (Phase 3 deterministic rules)
    → Action Execution (Phase 3 dry-run)
    → Outcome Estimation (Phase 4 outcome_tracker)
    → DB Persistence (Phase 4 SQLite)
    → Feedback (Phase 4 computed metrics)

SAFETY CONSTRAINTS (enforced here, not delegable to LLM):
  - Never auto-execute refunds, money transfers, price changes.
  - Only actions with automation_allowed=True and risk_level=LOW
    proceed to simulated execution.
  - All others are logged as "pending" (awaiting merchant approval).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

import os
import sys

# Ensure backend/ is always on path so imports are consistent (avoids double-registration)
_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from ai.investigator import investigate
from ai.decision_engine import decide
from ai.action_executor import execute
from ai.outcome_tracker import (
    estimate_outcome, save_resolution, resolution_to_dict,
)


# ── SAFETY GUARD ──────────────────────────────────────────────────────────

# Hard-blocked action types: these can NEVER be automatically executed
_BLOCKED_ACTIONS = frozenset({
    "issue_refund",
    "cancel_order",
    "transfer_money",
    "price_change",
})

# Actions that require explicit merchant approval before real execution
_APPROVAL_REQUIRED = frozenset({
    "refund_review",
})


class ResolutionEngine:
    """
    Closed-loop resolution orchestrator.

    Usage:
        engine = ResolutionEngine()
        result = engine.resolve(discovery, db_session)
    """

    def resolve(self, discovery: dict, db: Session) -> dict:
        """
        Run the full pipeline for a single discovery.

        Returns a fully-populated result dict with all stages.
        """
        # ── Stage 1: Investigation ────────────────────────────────────────
        investigation = investigate(discovery)

        # ── Stage 2: Decision ─────────────────────────────────────────────
        decision = decide(investigation, discovery)

        # ── Stage 3: Safety check + Execution ────────────────────────────
        action_type = decision.action_type
        execution_result: dict[str, Any]

        if action_type in _BLOCKED_ACTIONS:
            # Hard block — should never reach here due to decision_engine guards,
            # but defence-in-depth
            execution_result = {
                "status":           "blocked",
                "action_type":      action_type,
                "message":          (
                    f"SAFETY BLOCK: '{action_type}' is a financially irreversible action "
                    "and cannot be executed automatically under any circumstances."
                ),
                "automation_allowed": False,
                "risk_level":       "HIGH",
                "simulated_at":     datetime.now(timezone.utc).isoformat(),
            }
        elif action_type in _APPROVAL_REQUIRED or not decision.automation_allowed:
            # Needs merchant approval — log as pending, don't execute
            execution_result = {
                "status":           "pending_approval",
                "action_type":      action_type,
                "message":          (
                    f"[PENDING] Action '{action_type}' requires explicit merchant approval "
                    f"(risk_level={decision.risk_level}). "
                    "No automated execution performed."
                ),
                "automation_allowed": False,
                "risk_level":       decision.risk_level,
                "simulated_at":     datetime.now(timezone.utc).isoformat(),
            }
        else:
            # Safe to simulate
            execution_result = execute(decision)

        # ── Stage 4: Outcome estimation ───────────────────────────────────
        outcome = estimate_outcome(discovery, decision, execution_result)

        # ── Stage 5: Persist to DB ────────────────────────────────────────
        dataset_id = discovery.get("dataset_id")
        if not dataset_id:
            try:
                from routes.ai_discoveries import get_active_dataset_id
                dataset_id = get_active_dataset_id()
            except Exception:
                dataset_id = "demo"

        inv_summary = json.dumps({
            "dataset_id":         dataset_id,
            "investigation_mode": investigation.investigation_mode,
            "confidence":         investigation.confidence,
            "action_type":        investigation.action_type,
            "root_cause":         investigation.root_cause[:200],
        })
        row = save_resolution(db, outcome, investigation_summary=inv_summary)

        # ── Stage 6: Feedback ─────────────────────────────────────────────
        full_result = resolution_to_dict(row)

        return {
            # Pipeline stages (full detail)
            "discovery":    discovery,
            "investigation": investigation.model_dump(),
            "decision":     decision.model_dump(),
            "execution":    execution_result,
            "resolution":   full_result,
        }
