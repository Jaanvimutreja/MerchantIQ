"""
backend/ml/csv_normalizer.py

Validates and normalizes arbitrary merchant CSV transaction exports
(e.g., Shopify, Stripe, Razorpay, WooCommerce, or custom ERP)
into the MerchantIQ schema required by the DiscoveryEngine.
"""
from __future__ import annotations

import io
import re
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
import numpy as np


COLUMN_ALIASES: Dict[str, List[str]] = {
    "amount": [
        "amount", "total", "price", "transaction_amount", "order_amount",
        "order_value", "value", "net_amount", "gross_amount", "txn_amount",
        "amt", "cost", "charge_amount", "item_total", "grand_total"
    ],
    "payment_status": [
        "payment_status", "status", "payment_state", "transaction_status",
        "txn_status", "state", "charge_status", "result", "trans_status"
    ],
    "payment_method": [
        "payment_method", "method", "payment_mode", "mode", "payment_type",
        "gateway", "pay_mode", "payment_channel", "channel", "pay_type"
    ],
    "device_type": [
        "device_type", "device", "platform", "os", "client_type",
        "device_category", "client"
    ],
    "product_category": [
        "product_category", "category", "item_category", "product_type",
        "department", "vertical", "product_line"
    ],
    "location": [
        "location", "city", "region", "state", "country", "geo",
        "zone", "shipping_city", "billing_city"
    ],
    "timestamp": [
        "timestamp", "date", "created_at", "transaction_date", "time",
        "datetime", "order_date", "txn_date", "paid_at", "created_time"
    ],
    "cart_abandoned": [
        "cart_abandoned", "checkout_status", "cart_status", "abandoned", "is_abandoned", "abandonment",
        "cart_dropped", "dropped_cart", "checkout_state", "cart_state", "is_cart_abandoned",
        "abandoned_cart", "checkout_abandoned", "cart_exit"
    ],
    "refund_requested": [
        "refund_requested", "refund_status", "refunded", "is_refund", "has_refund",
        "refund_flag", "refund_state", "return_status", "is_refunded", "refund",
        "return_requested", "return_flag", "dispute_status"
    ],
    "retry_count": [
        "retry_count", "retries", "retry_attempts", "attempts",
        "attempt_count"
    ],
    "checkout_duration": [
        "checkout_duration", "duration", "time_spent", "session_duration",
        "time_taken", "duration_seconds"
    ],
    "order_id": [
        "order_id", "order_number", "order_no", "invoice_id", "id",
        "txn_id", "transaction_id", "reference_id"
    ],
    "customer_id": [
        "customer_id", "user_id", "buyer_id", "client_id", "customer_email",
        "email", "user"
    ],
    "merchant_id": [
        "merchant_id", "seller_id", "store_id", "vendor_id", "shop_id"
    ],
    "discount_given": [
        "discount_given", "discount", "discount_amount", "coupon_discount",
        "rebate", "applied_discount"
    ],
    "discount_requested": [
        "discount_requested", "requested_discount", "negotiated_discount"
    ],
    "negotiation_started": [
        "negotiation_started", "bargain_started", "negotiated", "bargain"
    ],
    "negotiation_rounds": [
        "negotiation_rounds", "rounds", "bargain_rounds"
    ],
    "final_order_status": [
        "final_order_status", "order_status", "fulfillment_status", "delivery_status"
    ],
    "failure_reason": [
        "failure_reason", "error_message", "reason", "decline_reason",
        "error_code", "status_detail"
    ],
}

REQUIRED_CANONICAL_COLUMNS = ["amount", "payment_status"]
REQUIRED_DIMENSION_COLUMNS = ["payment_method", "device_type", "product_category", "location"]

SUCCESS_VALUES = {
    "success", "completed", "captured", "paid", "authorized",
    "successful", "ok", "succeeded", "complete", "done", "true", "1"
}

FAILED_VALUES = {
    "failed", "failure", "declined", "error", "dropped",
    "rejected", "cancelled", "canceled", "unsuccessful", "false", "0"
}


ABANDONED_VALUES = {
    "true", "1", "yes", "y", "t",
    "abandoned", "dropped", "incomplete", "cart_abandoned", "checkout_abandoned",
    "bounced", "exit", "exited", "cancelled", "canceled", "left", "uncompleted", "drop"
}

REFUND_VALUES = {
    "true", "1", "yes", "y", "t",
    "refunded", "requested", "refund_requested", "returned", "return_requested",
    "chargeback", "disputed", "partially_refunded", "partial_refund", "refund", "reversal"
}


def _clean_header_name(header: str) -> str:
    """Lowercase, strip non-alphanumeric except underscore, and trim."""
    h = str(header).strip().lower()
    h = re.sub(r"[\s\-\.]+", "_", h)
    h = re.sub(r"[^\w]", "", h)
    return h


def _clean_amount_val(val: Any) -> float:
    """Parse raw amount string/number into positive float."""
    if pd.isna(val) or val is None or val == "":
        return 0.0
    if isinstance(val, (int, float)):
        return max(0.0, float(val))
    # String cleaning
    s = str(val).strip()
    s = re.sub(r"[₹\$,\s€£¥INR]", "", s, flags=re.IGNORECASE)
    try:
        return max(0.0, float(s))
    except ValueError:
        return 0.0


def _clean_status_val(val: Any) -> str:
    """Normalize status string to SUCCESS, FAILED, or PENDING."""
    if pd.isna(val) or val is None:
        return "SUCCESS"
    s = str(val).strip().lower()
    if s in SUCCESS_VALUES:
        return "SUCCESS"
    if s in FAILED_VALUES:
        return "FAILED"
    return "PENDING"


def _clean_bool_val(val: Any) -> bool:
    """Parse boolean flag safely."""
    if pd.isna(val) or val is None:
        return False
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return val > 0
    s = str(val).strip().lower()
    return s in {"true", "1", "yes", "y", "t"}


def _clean_cart_abandoned_val(val: Any) -> bool:
    """Parse cart/checkout abandonment boolean or status string."""
    if pd.isna(val) or val is None:
        return False
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return val > 0
    s = str(val).strip().lower()
    return s in ABANDONED_VALUES


def _clean_refund_val(val: Any) -> bool:
    """Parse refund boolean or status string."""
    if pd.isna(val) or val is None:
        return False
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return val > 0
    s = str(val).strip().lower()
    return s in REFUND_VALUES



def normalize_merchant_csv(
    file_content: bytes | str | io.StringIO | io.BytesIO,
    filename: str = "merchant_data.csv"
) -> Tuple[Optional[pd.DataFrame], Dict[str, Any], Optional[Dict[str, Any]]]:
    """
    Parse, validate, and normalize merchant CSV.
    
    Returns:
      (normalized_df, summary_dict, error_dict)
      If validation fails, normalized_df is None, summary_dict contains partial info,
      and error_dict contains the structured error description.
    """
    try:
        if isinstance(file_content, bytes):
            df_raw = pd.read_csv(io.BytesIO(file_content))
        elif isinstance(file_content, str):
            df_raw = pd.read_csv(io.StringIO(file_content))
        else:
            df_raw = pd.read_csv(file_content)
    except Exception as e:
        return None, {}, {
            "error_type": "CSV_PARSE_ERROR",
            "message": f"Unable to parse CSV file: {str(e)}",
            "missing_fields": [],
            "available_columns": [],
        }

    if len(df_raw) == 0:
        return None, {}, {
            "error_type": "EMPTY_CSV",
            "message": "The uploaded CSV file is empty.",
            "missing_fields": [],
            "available_columns": [],
        }

    # Minimum rows required for meaningful statistical discovery
    if len(df_raw) < 30:
        return None, {}, {
            "error_type": "INSUFFICIENT_DATA",
            "message": f"MerchantIQ requires at least 30 transaction records for statistical discovery (uploaded file has {len(df_raw)} rows).",
            "missing_fields": [],
            "available_columns": list(df_raw.columns),
        }

    # Map headers to canonical schema
    raw_columns = list(df_raw.columns)
    cleaned_col_map = {_clean_header_name(c): c for c in raw_columns}
    
    mapped_columns: Dict[str, str] = {}  # original_header -> canonical_field
    canonical_sources: Dict[str, str] = {}  # canonical_field -> original_header

    # Priority mapping
    for canonical_field, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            cleaned_alias = _clean_header_name(alias)
            if cleaned_alias in cleaned_col_map and canonical_field not in canonical_sources:
                orig_header = cleaned_col_map[cleaned_alias]
                if orig_header not in mapped_columns:
                    mapped_columns[orig_header] = canonical_field
                    canonical_sources[canonical_field] = orig_header
                    break

    # Validation: Check required fields
    missing_fields: List[str] = []
    for req in REQUIRED_CANONICAL_COLUMNS:
        if req not in canonical_sources:
            missing_fields.append(req)

    # Check at least one segmentation dimension
    has_any_dimension = any(dim in canonical_sources for dim in REQUIRED_DIMENSION_COLUMNS)
    if not has_any_dimension:
        missing_fields.append("at least one of (payment_method, device_type, product_category, location)")

    if missing_fields:
        return None, {}, {
            "error_type": "MISSING_REQUIRED_FIELDS",
            "message": (
                f"Missing required columns: {', '.join(missing_fields)}. "
                "MerchantIQ requires transaction amount, payment status, and at least one category dimension to detect friction."
            ),
            "missing_fields": missing_fields,
            "available_columns": raw_columns,
            "mapped_columns": mapped_columns,
            "required_fields_hint": {
                "amount": COLUMN_ALIASES["amount"][:5],
                "payment_status": COLUMN_ALIASES["payment_status"][:5],
                "dimension_examples": REQUIRED_DIMENSION_COLUMNS,
            },
        }

    # Build normalized DataFrame
    df_norm = pd.DataFrame(index=df_raw.index)

    # 1. Amount
    orig_amt_col = canonical_sources["amount"]
    df_norm["amount"] = df_raw[orig_amt_col].apply(_clean_amount_val)

    # 2. Payment Status
    orig_status_col = canonical_sources["payment_status"]
    df_norm["payment_status"] = df_raw[orig_status_col].apply(_clean_status_val)

    # 3. Payment Method
    if "payment_method" in canonical_sources:
        df_norm["payment_method"] = df_raw[canonical_sources["payment_method"]].fillna("Card").astype(str).str.strip()
    else:
        df_norm["payment_method"] = "Card"

    # 4. Device Type
    if "device_type" in canonical_sources:
        df_norm["device_type"] = df_raw[canonical_sources["device_type"]].fillna("Web").astype(str).str.strip()
    else:
        df_norm["device_type"] = "Web"

    # 5. Product Category
    if "product_category" in canonical_sources:
        df_norm["product_category"] = df_raw[canonical_sources["product_category"]].fillna("General").astype(str).str.strip()
    else:
        df_norm["product_category"] = "General"

    # 6. Location
    if "location" in canonical_sources:
        df_norm["location"] = df_raw[canonical_sources["location"]].fillna("National").astype(str).str.strip()
    else:
        df_norm["location"] = "National"

    # 7. Timestamp
    if "timestamp" in canonical_sources:
        df_norm["timestamp"] = pd.to_datetime(df_raw[canonical_sources["timestamp"]], errors="coerce").fillna(pd.Timestamp.now()).astype(str)
    else:
        # Generate realistic default timestamps
        base_time = pd.Timestamp.now() - pd.Timedelta(days=14)
        df_norm["timestamp"] = [
            str(base_time + pd.Timedelta(minutes=i * 2)) for i in range(len(df_raw))
        ]

    # 8. Numeric & Boolean Optional Attributes
    if "cart_abandoned" in canonical_sources:
        df_norm["cart_abandoned"] = df_raw[canonical_sources["cart_abandoned"]].apply(_clean_cart_abandoned_val)
    else:
        df_norm["cart_abandoned"] = False

    if "refund_requested" in canonical_sources:
        df_norm["refund_requested"] = df_raw[canonical_sources["refund_requested"]].apply(_clean_refund_val)
    else:
        df_norm["refund_requested"] = False

    # Check unmapped or alternative columns for abandonment / refund signals (e.g. checkout_status, order_status, refund_status)
    for c in raw_columns:
        c_clean = _clean_header_name(c)
        if ("checkout" in c_clean or "cart" in c_clean) and ("status" in c_clean or "state" in c_clean):
            df_norm["cart_abandoned"] = df_norm["cart_abandoned"] | df_raw[c].apply(_clean_cart_abandoned_val)
        elif ("refund" in c_clean or "return" in c_clean) and ("status" in c_clean or "state" in c_clean or "flag" in c_clean):
            df_norm["refund_requested"] = df_norm["refund_requested"] | df_raw[c].apply(_clean_refund_val)
        elif "order" in c_clean and ("status" in c_clean or "state" in c_clean):
            df_norm["cart_abandoned"] = df_norm["cart_abandoned"] | df_raw[c].apply(_clean_cart_abandoned_val)
            df_norm["refund_requested"] = df_norm["refund_requested"] | df_raw[c].apply(_clean_refund_val)

    if "retry_count" in canonical_sources:
        df_norm["retry_count"] = pd.to_numeric(df_raw[canonical_sources["retry_count"]], errors="coerce").fillna(0).astype(int)
    else:
        df_norm["retry_count"] = 0

    if "checkout_duration" in canonical_sources:
        df_norm["checkout_duration"] = pd.to_numeric(df_raw[canonical_sources["checkout_duration"]], errors="coerce").fillna(60).astype(int)
    else:
        df_norm["checkout_duration"] = 60

    if "discount_given" in canonical_sources:
        df_norm["discount_given"] = df_raw[canonical_sources["discount_given"]].apply(_clean_amount_val)
    else:
        df_norm["discount_given"] = 0.0

    if "discount_requested" in canonical_sources:
        df_norm["discount_requested"] = df_raw[canonical_sources["discount_requested"]].apply(_clean_amount_val)
    else:
        df_norm["discount_requested"] = 0.0

    if "negotiation_started" in canonical_sources:
        df_norm["negotiation_started"] = df_raw[canonical_sources["negotiation_started"]].apply(_clean_bool_val)
    else:
        df_norm["negotiation_started"] = False

    if "negotiation_rounds" in canonical_sources:
        df_norm["negotiation_rounds"] = pd.to_numeric(df_raw[canonical_sources["negotiation_rounds"]], errors="coerce").fillna(0).astype(int)
    else:
        df_norm["negotiation_rounds"] = 0

    if "final_order_status" in canonical_sources:
        df_norm["final_order_status"] = df_raw[canonical_sources["final_order_status"]].fillna("COMPLETED").astype(str).str.strip().str.upper()
    else:
        df_norm["final_order_status"] = np.where(df_norm["payment_status"] == "SUCCESS", "COMPLETED", "FAILED")

    # If abandoned or refunded, align final_order_status if default
    df_norm["final_order_status"] = np.where(df_norm["cart_abandoned"], "ABANDONED", df_norm["final_order_status"])

    if "failure_reason" in canonical_sources:
        df_norm["failure_reason"] = df_raw[canonical_sources["failure_reason"]].fillna("").astype(str).str.strip()
    else:
        df_norm["failure_reason"] = ""

    # Identifiers
    if "order_id" in canonical_sources:
        df_norm["order_id"] = df_raw[canonical_sources["order_id"]].fillna("").astype(str).str.strip()
    else:
        df_norm["order_id"] = [f"ord_{i:06d}" for i in range(1, len(df_raw) + 1)]

    if "customer_id" in canonical_sources:
        df_norm["customer_id"] = df_raw[canonical_sources["customer_id"]].fillna("").astype(str).str.strip()
    else:
        df_norm["customer_id"] = [f"cust_{i:04d}" for i in range(1, len(df_raw) + 1)]

    if "merchant_id" in canonical_sources:
        df_norm["merchant_id"] = df_raw[canonical_sources["merchant_id"]].fillna("merchant_upload").astype(str).str.strip()
    else:
        df_norm["merchant_id"] = "merchant_upload"

    df_norm["event_id"] = [f"evt_{i:06d}" for i in range(1, len(df_raw) + 1)]
    df_norm["refund_status"] = np.where(df_norm["refund_requested"], "REQUESTED", "NONE")

    # Unmapped columns list for transparency
    unmapped_columns = [c for c in raw_columns if c not in mapped_columns]

    summary = {
        "filename": filename,
        "total_records": len(df_norm),
        "total_volume": float(df_norm["amount"].sum()),
        "failed_transactions": int((df_norm["payment_status"] == "FAILED").sum()),
        "failure_rate": round(float((df_norm["payment_status"] == "FAILED").mean() * 100), 1),
        "abandoned_carts": int(df_norm["cart_abandoned"].sum()),
        "abandonment_rate": round(float(df_norm["cart_abandoned"].mean() * 100), 1),
        "refund_requests": int(df_norm["refund_requested"].sum()),
        "refund_rate": round(float(df_norm["refund_requested"].mean() * 100), 1),
        "mapped_columns": mapped_columns,
        "unmapped_columns": unmapped_columns,
        "detected_dimensions": [dim for dim in REQUIRED_DIMENSION_COLUMNS if dim in canonical_sources],
    }

    return df_norm, summary, None
