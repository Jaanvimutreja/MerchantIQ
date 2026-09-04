from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import AuditLog, Bargain
from schemas import AuditLogOut

router = APIRouter(tags=["Audit"])


@router.get("/bargains/{bargain_id}/audit", response_model=List[AuditLogOut])
def get_audit_log(bargain_id: int, db: Session = Depends(get_db)):
    bargain = db.query(Bargain).filter(Bargain.id == bargain_id).first()
    if not bargain:
        raise HTTPException(status_code=404, detail="Bargain not found")
    return (
        db.query(AuditLog)
        .filter(AuditLog.bargain_id == bargain_id)
        .order_by(AuditLog.created_at)
        .all()
    )
