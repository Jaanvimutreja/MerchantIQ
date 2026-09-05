"""
backend/routes/ai_investigations.py

Phase 3 API endpoints:

  POST /ai/investigate/{discovery_id}
      Pipeline: Discovery → Investigation → Decision → Safe Action Simulation

  GET  /ai/investigations
      Returns all completed investigations for discoveries in the active dataset.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

# Phase 2 discovery engine (no modification to Phase 2)
try:
    from backend.ml.discovery_engine import DiscoveryEngine
    from backend.routes.ai_discoveries import _cached_discoveries, get_discoveries, get_active_dataset_id
except ImportError:
    from ml.discovery_engine import DiscoveryEngine
    from routes.ai_discoveries import _cached_discoveries, get_discoveries, get_active_dataset_id

# Phase 3 AI layer
try:
    from backend.ai.investigator import investigate
    from backend.ai.decision_engine import decide
    from backend.ai.action_executor import execute
except ImportError:
    from ai.investigator import investigate
    from ai.decision_engine import decide
    from ai.action_executor import execute

router = APIRouter(prefix="/ai", tags=["ai"])

# In-memory investigation cache: discovery_id → full pipeline result
_investigations: Dict[str, Dict[str, Any]] = {}
_investigation_datasets: Dict[str, str] = {}


def clear_investigations() -> None:
    """Flush the in-memory investigation cache upon switching datasets."""
    global _investigations, _investigation_datasets
    _investigations.clear()
    _investigation_datasets.clear()


def _get_discovery(discovery_id: str) -> dict:
    """Retrieve a single discovery from the Phase 2 cache, loading if needed."""
    # Trigger Phase 2 cache load if not already done
    discoveries = get_discoveries()
    for d in discoveries:
        if d["discovery_id"] == discovery_id:
            return d
    raise HTTPException(status_code=404, detail=f"Discovery '{discovery_id}' not found")


@router.post("/investigate/{discovery_id}")
def investigate_discovery(discovery_id: str) -> Dict[str, Any]:
    """
    Full pipeline:
      1. Fetch discovery from Phase 2 engine
      2. AI Investigator (WHY)
      3. Decision Engine (WHAT TO DO)
      4. Action Executor (dry-run simulation)
    """
    # Step 1: Discovery
    discovery = _get_discovery(discovery_id)

    # Step 2: AI Investigation
    investigation = investigate(discovery)

    # Step 3: Decision
    decision = decide(investigation, discovery)

    # Step 4: Safe dry-run execution
    execution = execute(decision)

    result = {
        "discovery": discovery,
        "investigation": investigation.model_dump(),
        "decision": decision.model_dump(),
        "execution": execution,
    }

    # Cache result with active dataset tag
    active_ds_id = get_active_dataset_id()
    _investigations[discovery_id] = result
    _investigation_datasets[discovery_id] = active_ds_id
    return result


@router.get("/investigations")
def list_investigations() -> List[Dict[str, Any]]:
    """Return all investigations that have been run for discoveries in the active dataset."""
    active_ds_id = get_active_dataset_id()
    active_ids = {d["discovery_id"] for d in get_discoveries()}
    return [
        v for k, v in _investigations.items()
        if k in active_ids and _investigation_datasets.get(k, "demo") == active_ds_id
    ]
