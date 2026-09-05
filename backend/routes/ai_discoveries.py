"""
backend/routes/ai_discoveries.py

FastAPI router for MerchantIQ AI Discovery Engine.
Supports:
  - GET /ai/discoveries: Retrieve active discoveries (default demo or uploaded merchant CSV)
  - GET /ai/discoveries/{discovery_id}: Retrieve single discovery by ID
  - POST /ai/analyze-csv (and alias /ai/upload-csv): Upload custom merchant CSV, validate & map columns,
    run DiscoveryEngine, update cache, clear previous session state, and return summary + discoveries
  - POST /ai/reset-demo: Revert back to the 10,000-record synthetic demo dataset
  - GET /ai/dataset-info: Active dataset metadata (is_custom, filename, records, mapped columns, live revenue at risk and recovered revenue)
"""
from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from database import get_db

try:
    from backend.ml.discovery_engine import DiscoveryEngine
    from backend.ml.csv_normalizer import normalize_merchant_csv
except ImportError:
    from ml.discovery_engine import DiscoveryEngine
    from ml.csv_normalizer import normalize_merchant_csv

# Resolve default CSV path relative to this file's location (backend/routes/ -> backend/data/)
_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_CSV_PATH = str(_DATA_DIR / "merchant_events.csv")
_TEMP_UPLOAD_PATH = str(_DATA_DIR / "temp_merchant_upload.csv")

router = APIRouter(prefix="/ai", tags=["ai"])

_cached_discoveries: Optional[List[Dict[str, Any]]] = None
_current_dataset_info: Optional[Dict[str, Any]] = None
_active_dataset_id: str = "demo"


def get_active_dataset_id() -> str:
    """Return the active dataset session ID ('demo' or 'custom_<uuid>')."""
    global _active_dataset_id
    return _active_dataset_id


def _get_demo_info(discoveries: List[Dict[str, Any]], recovered_revenue: float = 0.0, resolved_count: int = 0) -> Dict[str, Any]:
    rev_risk = sum(d.get("estimated_revenue_at_risk", 0.0) for d in discoveries)
    return {
        "is_custom": False,
        "dataset_id": "demo",
        "filename": "merchant_events.csv",
        "total_records": 10000,
        "total_volume": 35704812.0,
        "failure_rate": 8.5,
        "problems_discovered": len(discoveries),
        "revenue_at_risk": rev_risk,
        "recovered_revenue": recovered_revenue,
        "resolved_count": resolved_count,
        "mapped_columns": {},
        "unmapped_columns": [],
        "detected_dimensions": ["payment_method", "device_type", "product_category", "location"],
    }


@router.get("/discoveries")
def get_discoveries() -> List[Dict[str, Any]]:
    global _cached_discoveries, _current_dataset_info, _active_dataset_id
    if _cached_discoveries is None:
        if not os.path.exists(_CSV_PATH):
            raise HTTPException(status_code=404, detail=f"Default data file not found: {_CSV_PATH}")
        engine = DiscoveryEngine()
        _cached_discoveries = engine.run(_CSV_PATH)
        _active_dataset_id = "demo"
        _current_dataset_info = _get_demo_info(_cached_discoveries)
    return _cached_discoveries


@router.get("/discoveries/{discovery_id}")
def get_discovery(discovery_id: str) -> Dict[str, Any]:
    global _cached_discoveries
    if _cached_discoveries is None:
        get_discoveries()  # load cache
        
    for d in _cached_discoveries:  # type: ignore[union-attr]
        if d.get("discovery_id") == discovery_id:
            return d
    raise HTTPException(status_code=404, detail=f"Discovery not found: {discovery_id}")


@router.get("/dataset-info")
def get_dataset_info(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Return active dataset metadata with accurate revenue at risk and recovered revenue."""
    global _current_dataset_info, _active_dataset_id
    if _current_dataset_info is None:
        get_discoveries()

    info = dict(_current_dataset_info or {})
    
    # Calculate live recovered revenue & resolved count for the active dataset scope
    try:
        from routes.ai_resolutions import get_resolutions
        active_resolutions = get_resolutions(db)
        info["recovered_revenue"] = sum(r.get("recovered_amount", 0.0) for r in active_resolutions)
        info["resolved_count"] = len(active_resolutions)
    except Exception:
        info["recovered_revenue"] = 0.0
        info["resolved_count"] = 0

    return info


@router.post("/analyze-csv")
@router.post("/upload-csv")
async def analyze_merchant_csv_endpoint(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Accept merchant transaction CSV, normalize & map columns, validate required schema,
    run ML discovery engine, update active discoveries, clear previous session state,
    and return summary + discoveries.
    """
    global _cached_discoveries, _current_dataset_info, _active_dataset_id

    if not file.filename:
        raise HTTPException(status_code=400, detail={"message": "No file uploaded or missing filename."})

    if not file.filename.lower().endswith((".csv", ".txt")):
        raise HTTPException(
            status_code=400,
            detail={
                "error_type": "INVALID_FILE_TYPE",
                "message": f"Expected a CSV file, but received '{file.filename}'. Please upload a valid .csv file.",
            },
        )

    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={"error_type": "FILE_READ_ERROR", "message": f"Could not read uploaded file: {str(e)}"},
        )

    # 1. Normalize and validate against MerchantIQ transaction schema
    df_norm, summary, error_dict = normalize_merchant_csv(content, filename=file.filename)

    if error_dict is not None or df_norm is None:
        # Return 422 with clear structural feedback
        raise HTTPException(status_code=422, detail=error_dict)

    # 2. Save normalized data temporarily
    try:
        os.makedirs(_DATA_DIR, exist_ok=True)
        df_norm.to_csv(_TEMP_UPLOAD_PATH, index=False)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error_type": "STORAGE_ERROR", "message": f"Failed to cache normalized dataset: {str(e)}"},
        )

    # 3. Run DiscoveryEngine on normalized data
    try:
        engine = DiscoveryEngine()
        discoveries = engine.run(_TEMP_UPLOAD_PATH)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error_type": "ANALYSIS_ERROR", "message": f"ML Discovery Engine failed on uploaded data: {str(e)}"},
        )

    # 4. Generate new session ID for custom dataset
    _active_dataset_id = f"custom_{uuid.uuid4().hex[:8]}"

    # Tag each discovery with the active custom dataset_id
    for d in discoveries:
        d["dataset_id"] = _active_dataset_id

    # 5. Clear previous in-memory investigations
    try:
        from routes.ai_investigations import clear_investigations
        clear_investigations()
    except Exception:
        pass

    # 6. Update cache and dataset info (Revenue Recovered is strictly 0.0 for a fresh upload)
    _cached_discoveries = discoveries
    total_rev_at_risk = sum(d.get("estimated_revenue_at_risk", 0.0) for d in discoveries)

    _current_dataset_info = {
        "is_custom": True,
        "dataset_id": _active_dataset_id,
        "filename": file.filename,
        "total_records": summary["total_records"],
        "total_volume": summary["total_volume"],
        "failed_transactions": summary["failed_transactions"],
        "failure_rate": summary["failure_rate"],
        "problems_discovered": len(discoveries),
        "revenue_at_risk": total_rev_at_risk,
        "recovered_revenue": 0.0,
        "resolved_count": 0,
        "mapped_columns": summary["mapped_columns"],
        "unmapped_columns": summary["unmapped_columns"],
        "detected_dimensions": summary["detected_dimensions"],
    }

    return {
        "status": "success",
        "summary": _current_dataset_info,
        "discoveries": discoveries,
    }


@router.post("/reset-demo")
def reset_to_demo_dataset(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Revert back to the default 10,000 synthetic merchant events dataset."""
    global _cached_discoveries, _current_dataset_info, _active_dataset_id

    # Remove temporary uploaded CSV if exists
    if os.path.exists(_TEMP_UPLOAD_PATH):
        try:
            os.remove(_TEMP_UPLOAD_PATH)
        except OSError:
            pass

    if not os.path.exists(_CSV_PATH):
        raise HTTPException(status_code=404, detail=f"Default data file not found: {_CSV_PATH}")

    # Set active dataset to demo
    _active_dataset_id = "demo"

    # Clear investigations cache
    try:
        from routes.ai_investigations import clear_investigations
        clear_investigations()
    except Exception:
        pass

    engine = DiscoveryEngine()
    _cached_discoveries = engine.run(_CSV_PATH)
    for d in _cached_discoveries:
        d["dataset_id"] = "demo"

    # Calculate demo recovered revenue if demo resolutions exist
    recovered_amount = 0.0
    resolved_count = 0
    try:
        from routes.ai_resolutions import get_resolutions
        demo_res = get_resolutions(db)
        recovered_amount = sum(r.get("recovered_amount", 0.0) for r in demo_res)
        resolved_count = len(demo_res)
    except Exception:
        pass

    _current_dataset_info = _get_demo_info(_cached_discoveries, recovered_revenue=recovered_amount, resolved_count=resolved_count)

    return {
        "status": "success",
        "message": "Successfully reverted to default demo dataset.",
        "summary": _current_dataset_info,
        "discoveries": _cached_discoveries,
    }
