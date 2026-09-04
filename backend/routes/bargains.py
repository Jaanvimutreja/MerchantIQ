import os
import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from models import Bargain, BargainStatus, Product, AuditLog, Offer, OfferStatus
from schemas import BargainCreate, BargainOut, RecommendationOut, OfferActionRequest, ApprovalOut

router = APIRouter(prefix="/bargains", tags=["Bargains"])


@router.post("/", response_model=BargainOut, status_code=201)
def create_bargain(payload: BargainCreate, db: Session = Depends(get_db)):
    # Validate product exists
    product = db.query(Product).filter(Product.id == payload.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if payload.min_price > product.original_price:
        raise HTTPException(
            status_code=400,
            detail="min_price cannot exceed the product's original_price",
        )

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    expires_at = now + timedelta(hours=payload.duration_hours)

    bargain = Bargain(
        product_id=product.id,
        original_price=product.original_price,
        min_price=payload.min_price,
        duration_hours=payload.duration_hours,
        expires_at=expires_at,
        audience=payload.audience,
        objective=payload.objective,
        status=BargainStatus.ACTIVE,
        version=1,
    )
    db.add(bargain)
    db.flush()  # get bargain.id before audit log

    audit = AuditLog(
        bargain_id=bargain.id,
        event="bargain_created",
        details=f"Bargain created for product '{product.name}' (id={product.id}). "
                f"Price range: {payload.min_price}–{product.original_price}. "
                f"Expires at {expires_at.isoformat()}.",
    )
    db.add(audit)
    db.commit()
    db.refresh(bargain)
    return bargain


@router.get("/", response_model=List[BargainOut])
def list_bargains(db: Session = Depends(get_db)):
    bargains = db.query(Bargain).all()
    _check_expirations(bargains, db)
    return bargains


@router.get("/{bargain_id}", response_model=BargainOut)
def get_bargain(bargain_id: int, db: Session = Depends(get_db)):
    bargain = db.query(Bargain).filter(Bargain.id == bargain_id).first()
    if not bargain:
        raise HTTPException(status_code=404, detail="Bargain not found")
    _check_expirations([bargain], db)
    return bargain


# ── AI Deal Strategist Helpers ───────────────────────────────

def _call_gemini_flash(
    bargain: Bargain,
    pending_offers: List[Offer],
    api_key: str,
) -> dict:
    """Call Google Gemini Flash via Generative Language API.

    Returns parsed JSON with recommended_offer_id, confidence, reasoning.
    Raises Exception on any failure.
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    time_left_sec = max(0, (bargain.expires_at - now).total_seconds())
    time_left_hours = round(time_left_sec / 3600, 1)

    product_name = bargain.product.name if bargain.product else f"Product #{bargain.product_id}"
    inventory = bargain.product.inventory if bargain.product else 0

    offers_data = [
        {
            "offer_id": o.id,
            "customer_name": o.customer_name,
            "offered_price": o.offered_price,
            "created_at": o.created_at.isoformat() if o.created_at else "",
        }
        for o in pending_offers
    ]

    prompt = (
        "You are an AI Deal Strategist for an e-commerce bargaining platform called BargainAI.\n"
        "Your task is to analyze real customer offers for a limited-time bargain and recommend the single best offer for the merchant to consider.\n"
        "IMPORTANT: You only recommend — you NEVER approve the offer. The merchant makes the final decision.\n\n"
        f"BARGAIN CONTEXT:\n"
        f"- Product: {product_name}\n"
        f"- Original Price: ₹{bargain.original_price}\n"
        f"- Minimum Acceptable Price: ₹{bargain.min_price}\n"
        f"- Inventory: {inventory} units\n"
        f"- Merchant Objective: {bargain.objective or 'Maximize Revenue'}\n"
        f"- Target Audience: {bargain.audience or 'Everyone'}\n"
        f"- Time Remaining: {time_left_hours} hours\n\n"
        f"CANDIDATE OFFERS (Real pending offers from database):\n"
        f"{json.dumps(offers_data, indent=2)}\n\n"
        "STRATEGY GUIDELINES based on merchant objective:\n"
        "- 'Clear Inventory': Prioritize solid offers quickly to guarantee sales velocity.\n"
        "- 'Maximize Revenue': Prioritize highest offered prices closest to original price.\n"
        "- 'Drive Customer Engagement': Balance fair price with rewarding high-intent customers.\n\n"
        "REQUIREMENTS:\n"
        "1. You MUST choose exactly ONE offer_id from the candidate offers above.\n"
        "2. The recommended_offer_id MUST be an integer matching one of the candidate offer_id values.\n"
        "3. Provide a confidence score between 0.0 and 1.0.\n"
        "4. Provide a clear, concise reasoning explaining why this specific offer best satisfies the merchant's objective.\n\n"
        "Return ONLY a JSON object with this exact schema:\n"
        "{\n"
        '  "recommended_offer_id": <int>,\n'
        '  "confidence": <float between 0.0 and 1.0>,\n'
        '  "reasoning": "<concise explanation>"\n'
        "}"
    )

    body = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json",
        },
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=12) as resp:
        resp_data = json.loads(resp.read().decode("utf-8"))
        raw_text = resp_data["candidates"][0]["content"]["parts"][0]["text"]
        result = json.loads(raw_text)
        return result


def _deterministic_fallback(bargain: Bargain, pending_offers: List[Offer]) -> dict:
    """Deterministic fallback: select highest real eligible pending offer."""
    # Highest offered price; tie-break on earliest id
    best_offer = max(pending_offers, key=lambda o: (o.offered_price, -o.id))

    ratio = best_offer.offered_price / bargain.original_price if bargain.original_price > 0 else 0.5
    confidence = round(min(1.0, max(0.5, ratio)), 2)

    reasoning = (
        f"Deterministic fallback: Selected highest eligible pending offer of "
        f"₹{best_offer.offered_price:.2f} from {best_offer.customer_name} "
        f"to satisfy merchant objective '{bargain.objective or 'Maximize Revenue'}'."
    )
    return {
        "recommended_offer_id": best_offer.id,
        "confidence": confidence,
        "reasoning": reasoning,
        "is_fallback": True,
        "customer_name": best_offer.customer_name,
        "offered_price": best_offer.offered_price,
    }


# ── AI Recommendation Route ───────────────────────────────────

@router.get("/{bargain_id}/recommendation", response_model=RecommendationOut, tags=["AI"])
def get_recommendation(bargain_id: int, db: Session = Depends(get_db)):
    """AI Deal Strategist: evaluates real pending offers and recommends the best one."""
    bargain = db.query(Bargain).filter(Bargain.id == bargain_id).first()
    if not bargain:
        raise HTTPException(status_code=404, detail="Bargain not found")

    # Auto-expire check and active status validation
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if bargain.status == BargainStatus.ACTIVE and bargain.expires_at <= now:
        bargain.status = BargainStatus.EXPIRED
        db.commit()

    if bargain.status != BargainStatus.ACTIVE:
        raise HTTPException(
            status_code=400,
            detail=f"Bargain is not active (current status: {bargain.status.value})",
        )

    # Load all real pending offers
    pending_offers = (
        db.query(Offer)
        .filter(Offer.bargain_id == bargain_id, Offer.status == OfferStatus.PENDING)
        .all()
    )
    if not pending_offers:
        raise HTTPException(
            status_code=400,
            detail="No pending offers available for recommendation",
        )

    api_key = os.getenv("AI_API_KEY", "").strip()
    valid_ids = {o.id for o in pending_offers}
    rec_data = None

    if api_key:
        try:
            raw_rec = _call_gemini_flash(bargain, pending_offers, api_key)
            rec_id = int(raw_rec.get("recommended_offer_id", 0))
            if rec_id in valid_ids:
                rec_offer = next(o for o in pending_offers if o.id == rec_id)
                conf = float(raw_rec.get("confidence", 0.85))
                conf = max(0.0, min(1.0, conf))
                rec_data = {
                    "recommended_offer_id": rec_id,
                    "confidence": round(conf, 2),
                    "reasoning": str(raw_rec.get("reasoning", "")),
                    "is_fallback": False,
                    "customer_name": rec_offer.customer_name,
                    "offered_price": rec_offer.offered_price,
                }
        except Exception:
            # On any Gemini failure or timeout, activate deterministic fallback
            rec_data = None

    if rec_data is None:
        rec_data = _deterministic_fallback(bargain, pending_offers)

    # Log real database AuditLog record
    audit = AuditLog(
        bargain_id=bargain.id,
        event="ai_recommendation_generated",
        details=(
            f"Recommended Offer ID: {rec_data['recommended_offer_id']} | "
            f"Customer: {rec_data['customer_name']} (₹{rec_data['offered_price']}) | "
            f"Confidence: {rec_data['confidence']} | "
            f"Fallback: {rec_data['is_fallback']} | "
            f"Reasoning: {rec_data['reasoning']}"
        ),
    )
    db.add(audit)
    db.commit()

    return RecommendationOut(**rec_data)


@router.post("/{bargain_id}/approve", response_model=ApprovalOut, tags=["Merchant Approval"])
def approve_bargain(bargain_id: int, payload: OfferActionRequest, db: Session = Depends(get_db)):
    """Atomic approval of an eligible offer with optimistic concurrency locking."""
    bargain = db.query(Bargain).filter(Bargain.id == bargain_id).first()
    if not bargain:
        raise HTTPException(status_code=404, detail="Bargain not found")

    # Check auto-expiration
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if bargain.status == BargainStatus.ACTIVE and bargain.expires_at <= now:
        bargain.status = BargainStatus.EXPIRED
        db.commit()
        raise HTTPException(status_code=400, detail="Bargain has expired")

    if bargain.status == BargainStatus.APPROVED:
        raise HTTPException(status_code=409, detail="Conflict: Bargain is already approved")

    if bargain.status != BargainStatus.ACTIVE:
        raise HTTPException(
            status_code=400,
            detail=f"Bargain is not active (current status: {bargain.status.value})",
        )

    # Validate offer
    offer = db.query(Offer).filter(Offer.id == payload.offer_id).first()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")

    if offer.bargain_id != bargain.id:
        raise HTTPException(status_code=400, detail="Offer does not belong to this bargain")

    if offer.status != OfferStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Offer is not pending (current status: {offer.status.value})",
        )

    if offer.offered_price < bargain.min_price or offer.offered_price > bargain.original_price:
        raise HTTPException(
            status_code=400,
            detail=f"Offered price (₹{offer.offered_price}) is outside the bargain's valid range (₹{bargain.min_price}–₹{bargain.original_price})",
        )

    expected_version = bargain.version

    # ATOMIC OPTIMISTIC LOCKING:
    # Update bargain status to APPROVED and increment version ONLY IF version and status match
    rows_updated = (
        db.query(Bargain)
        .filter(
            Bargain.id == bargain_id,
            Bargain.version == expected_version,
            Bargain.status == BargainStatus.ACTIVE,
        )
        .update(
            {
                Bargain.status: BargainStatus.APPROVED,
                Bargain.version: Bargain.version + 1,
            },
            synchronize_session=False,
        )
    )

    if rows_updated == 0:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Conflict: Bargain was already approved or modified by another concurrent request",
        )

    # Atomically mark selected offer as APPROVED
    offer_updated = (
        db.query(Offer)
        .filter(Offer.id == payload.offer_id, Offer.status == OfferStatus.PENDING)
        .update({Offer.status: OfferStatus.APPROVED}, synchronize_session=False)
    )

    if offer_updated == 0:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Conflict: Selected offer was already processed by another request",
        )

    # Set every other PENDING offer for that bargain to REJECTED
    db.query(Offer).filter(
        Offer.bargain_id == bargain_id,
        Offer.id != payload.offer_id,
        Offer.status == OfferStatus.PENDING,
    ).update({Offer.status: OfferStatus.REJECTED}, synchronize_session=False)

    # Create real audit log
    audit = AuditLog(
        bargain_id=bargain.id,
        event="merchant_offer_approved",
        details=(
            f"Offer #{offer.id} approved by merchant for ₹{offer.offered_price:.2f} "
            f"(Customer: {offer.customer_name}, Email: {offer.customer_email}). "
            f"All other pending offers rejected."
        ),
    )
    db.add(audit)

    # Commit the entire transaction atomically
    db.commit()

    return {
        "message": "Offer approved successfully",
        "bargain_id": bargain.id,
        "approved_offer_id": offer.id,
        "status": BargainStatus.APPROVED.value,
        "version": expected_version + 1,
    }


@router.post("/{bargain_id}/reject", tags=["Merchant Approval"])
def reject_bargain(bargain_id: int, payload: OfferActionRequest, db: Session = Depends(get_db)):
    """Reject a specific single PENDING offer."""
    bargain = db.query(Bargain).filter(Bargain.id == bargain_id).first()
    if not bargain:
        raise HTTPException(status_code=404, detail="Bargain not found")

    offer = db.query(Offer).filter(Offer.id == payload.offer_id).first()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")

    if offer.bargain_id != bargain.id:
        raise HTTPException(status_code=400, detail="Offer does not belong to this bargain")

    if offer.status != OfferStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot reject offer with status '{offer.status.value}'. Only PENDING offers can be rejected.",
        )

    offer.status = OfferStatus.REJECTED

    audit = AuditLog(
        bargain_id=bargain.id,
        event="merchant_offer_rejected",
        details=(
            f"Offer #{offer.id} rejected by merchant "
            f"(Customer: {offer.customer_name}, Amount: ₹{offer.offered_price:.2f})."
        ),
    )
    db.add(audit)
    db.commit()

    return {
        "message": "Offer rejected successfully",
        "offer_id": offer.id,
        "status": OfferStatus.REJECTED.value,
    }


# ── Helpers ───────────────────────────────────────────────────

def _check_expirations(bargains: list[Bargain], db: Session):
    """Auto-expire ACTIVE bargains past their expires_at."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    changed = False
    for b in bargains:
        if b.status == BargainStatus.ACTIVE and b.expires_at <= now:
            b.status = BargainStatus.EXPIRED
            changed = True
    if changed:
        db.commit()
