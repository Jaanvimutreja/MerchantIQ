"""
backend/routes/ai_resolutions.py

Phase 4 API endpoints:

  POST /ai/resolve/{discovery_id}
      Full closed-loop pipeline:
      Discovery → Investigation → Decision → Resolution → Outcome → Feedback

  GET  /ai/resolutions
      List resolutions scoped to the currently active dataset.

  GET  /ai/resolutions/{resolution_id}
      Retrieve a single resolution with feedback metrics.
"""
from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db

# Ensure backend/ is on path for consistent single-module registration
_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from ai.resolution_engine import ResolutionEngine
from ai.outcome_tracker import (
    get_resolution, list_resolutions, resolution_to_dict,
)
from routes.ai_discoveries import get_discoveries, get_active_dataset_id

router = APIRouter(prefix="/ai", tags=["ai"])
_engine = ResolutionEngine()


def _fetch_discovery(discovery_id: str) -> dict:
    """Fetch a discovery from the Phase 2 engine cache."""
    discoveries = get_discoveries()
    for d in discoveries:
        if d["discovery_id"] == discovery_id:
            return d
    raise HTTPException(
        status_code=404,
        detail=f"Discovery '{discovery_id}' not found. "
               "Call GET /ai/discoveries first to load the discovery cache.",
    )


@router.post("/resolve/{discovery_id}")
def resolve_discovery(
    discovery_id: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Full closed-loop pipeline for a single discovery.
    Returns the complete pipeline trace: discovery → investigation →
    decision → execution → resolution (with feedback).
    """
    discovery = _fetch_discovery(discovery_id)
    result = _engine.resolve(discovery, db)
    return result


@router.get("/resolutions")
def get_resolutions(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """List resolutions scoped to the currently active dataset, most recent first."""
    try:
        active_dataset_id = get_active_dataset_id()
    except Exception:
        active_dataset_id = "demo"

    discoveries = get_discoveries()
    active_ids = {d["discovery_id"] for d in discoveries}

    rows = list_resolutions(db)
    matching = []
    for r in rows:
        r_dataset_id = None
        if r.investigation_summary:
            try:
                parsed = json.loads(r.investigation_summary)
                if isinstance(parsed, dict):
                    r_dataset_id = parsed.get("dataset_id")
            except Exception:
                pass

        if active_dataset_id == "demo":
            # In demo mode: accept resolutions tagged 'demo' or legacy rows whose discovery_id matches active demo
            if (r_dataset_id is None or r_dataset_id == "demo") and r.discovery_id in active_ids:
                matching.append(resolution_to_dict(r))
        else:
            # In custom mode: accept ONLY resolutions executed on this specific uploaded dataset
            if r_dataset_id == active_dataset_id and r.discovery_id in active_ids:
                matching.append(resolution_to_dict(r))

    return matching


@router.get("/resolutions/{resolution_id}")
def get_resolution_by_id(
    resolution_id: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Retrieve a single resolution with its feedback metrics."""
    row = get_resolution(db, resolution_id)
    if not row:
        raise HTTPException(
            status_code=404,
            detail=f"Resolution '{resolution_id}' not found.",
        )
    return resolution_to_dict(row)
