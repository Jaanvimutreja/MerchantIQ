from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ── Product ───────────────────────────────────────────────────

class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1)
    original_price: float = Field(..., gt=0)
    inventory: int = Field(..., ge=0)


class ProductOut(BaseModel):
    id: int
    name: str
    original_price: float
    inventory: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Bargain ───────────────────────────────────────────────────

class BargainCreate(BaseModel):
    product_id: int
    min_price: float = Field(..., gt=0)
    duration_hours: int = Field(..., gt=0)
    audience: Optional[str] = None
    objective: Optional[str] = None


class BargainOut(BaseModel):
    id: int
    product_id: int
    original_price: float
    min_price: float
    duration_hours: int
    expires_at: datetime
    audience: Optional[str]
    objective: Optional[str]
    status: str
    version: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Offer ─────────────────────────────────────────────────────

class OfferCreate(BaseModel):
    customer_name: str = Field(..., min_length=1)
    customer_email: str = Field(..., min_length=1)   # basic validation; no extra dep
    offered_price: float = Field(..., gt=0)


class OfferOut(BaseModel):
    id: int
    bargain_id: int
    customer_name: str
    customer_email: str
    offered_price: float
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Audit ─────────────────────────────────────────────────────

class AuditLogOut(BaseModel):
    id: int
    bargain_id: int
    event: str
    details: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ── AI Recommendation ─────────────────────────────────────────

class RecommendationOut(BaseModel):
    recommended_offer_id: int
    confidence: float
    reasoning: str
    is_fallback: bool = False
    customer_name: Optional[str] = None
    offered_price: Optional[float] = None
