from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import Bargain, BargainStatus, Product, AuditLog
from schemas import BargainCreate, BargainOut

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
