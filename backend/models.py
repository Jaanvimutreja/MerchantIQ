import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from database import Base


# ── Status enums ──────────────────────────────────────────────

class BargainStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    APPROVED = "APPROVED"
    COMPLETED = "COMPLETED"


class OfferStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


# ── Models ────────────────────────────────────────────────────

def _utcnow() -> datetime:
    """Naive UTC datetime — SQLite does not store timezone info."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    original_price = Column(Float, nullable=False)
    inventory = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=_utcnow)

    bargains = relationship("Bargain", back_populates="product")


class Bargain(Base):
    __tablename__ = "bargains"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    original_price = Column(Float, nullable=False)
    min_price = Column(Float, nullable=False)
    duration_hours = Column(Integer, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    audience = Column(String, nullable=True)
    objective = Column(String, nullable=True)
    status = Column(SAEnum(BargainStatus), default=BargainStatus.ACTIVE, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=_utcnow)

    product = relationship("Product", back_populates="bargains")
    offers = relationship("Offer", back_populates="bargain")
    payments = relationship("Payment", back_populates="bargain")
    audit_logs = relationship("AuditLog", back_populates="bargain")


class Offer(Base):
    __tablename__ = "offers"

    id = Column(Integer, primary_key=True, index=True)
    bargain_id = Column(Integer, ForeignKey("bargains.id"), nullable=False)
    customer_name = Column(String, nullable=False)
    customer_email = Column(String, nullable=False)
    offered_price = Column(Float, nullable=False)
    status = Column(SAEnum(OfferStatus), default=OfferStatus.PENDING, nullable=False)
    created_at = Column(DateTime, default=_utcnow)

    bargain = relationship("Bargain", back_populates="offers")
    payments = relationship("Payment", back_populates="offer")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    bargain_id = Column(Integer, ForeignKey("bargains.id"), nullable=False)
    offer_id = Column(Integer, ForeignKey("offers.id"), nullable=False)
    razorpay_order_id = Column(String, nullable=True)
    razorpay_payment_id = Column(String, nullable=True)
    amount = Column(Float, nullable=False)
    status = Column(SAEnum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    created_at = Column(DateTime, default=_utcnow)

    bargain = relationship("Bargain", back_populates="payments")
    offer = relationship("Offer", back_populates="payments")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    bargain_id = Column(Integer, ForeignKey("bargains.id"), nullable=False)
    event = Column(String, nullable=False)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    bargain = relationship("Bargain", back_populates="audit_logs")
