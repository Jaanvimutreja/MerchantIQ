from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import Offer, Bargain, BargainStatus, OfferStatus, AuditLog
from schemas import OfferCreate, OfferOut

router = APIRouter(tags=["Offers"])


@router.post("/bargains/{bargain_id}/offers", response_model=OfferOut, status_code=201)
def create_offer(bargain_id: int, payload: OfferCreate, db: Session = Depends(get_db)):
    bargain = db.query(Bargain).filter(Bargain.id == bargain_id).first()
    if not bargain:
        raise HTTPException(status_code=404, detail="Bargain not found")

    # Auto-detect expiration
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if bargain.status == BargainStatus.ACTIVE and bargain.expires_at <= now:
        bargain.status = BargainStatus.EXPIRED
        db.commit()

    if bargain.status != BargainStatus.ACTIVE:
        raise HTTPException(
            status_code=400,
            detail=f"Bargain is not active (current status: {bargain.status.value})",
        )

    if payload.offered_price < bargain.min_price:
        raise HTTPException(
            status_code=400,
            detail=f"Offered price ({payload.offered_price}) is below the minimum ({bargain.min_price})",
        )

    if payload.offered_price > bargain.original_price:
        raise HTTPException(
            status_code=400,
            detail=f"Offered price ({payload.offered_price}) exceeds the original price ({bargain.original_price})",
        )

    offer = Offer(
        bargain_id=bargain.id,
        customer_name=payload.customer_name,
        customer_email=payload.customer_email,
        offered_price=payload.offered_price,
        status=OfferStatus.PENDING,
    )
    db.add(offer)
    db.flush()

    audit = AuditLog(
        bargain_id=bargain.id,
        event="offer_received",
        details=f"Offer #{offer.id} from {payload.customer_name} ({payload.customer_email}) "
                f"for ₹{payload.offered_price}.",
    )
    db.add(audit)
    db.commit()
    db.refresh(offer)
    return offer


@router.get("/bargains/{bargain_id}/offers", response_model=List[OfferOut])
def list_offers(bargain_id: int, db: Session = Depends(get_db)):
    bargain = db.query(Bargain).filter(Bargain.id == bargain_id).first()
    if not bargain:
        raise HTTPException(status_code=404, detail="Bargain not found")
    return db.query(Offer).filter(Offer.bargain_id == bargain_id).all()
