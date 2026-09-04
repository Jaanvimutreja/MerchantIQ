import base64
import hashlib
import hmac
import json
import os
import urllib.error
import urllib.request
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from database import get_db
from models import AuditLog, Bargain, BargainStatus, Offer, OfferStatus, Payment, PaymentStatus
from schemas import CreateOrderRequest, CreateOrderResponse

router = APIRouter(prefix="/payments", tags=["Payments"])


def create_razorpay_order_api(key_id: str, key_secret: str, amount_paise: int, receipt: str, notes: dict) -> dict:
    """Call real Razorpay Test Mode API to create an order.
    Can be mocked in automated unit/integration tests.
    """
    url = "https://api.razorpay.com/v1/orders"
    payload = {
        "amount": amount_paise,
        "currency": "INR",
        "receipt": receipt,
        "notes": notes,
    }
    auth_str = f"{key_id}:{key_secret}"
    auth_b64 = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Basic {auth_b64}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            err_json = json.loads(err_body)
            err_desc = err_json.get("error", {}).get("description", err_body)
        except Exception:
            err_desc = err_body
        raise HTTPException(
            status_code=502,
            detail=f"Razorpay order creation failed ({e.code}): {err_desc}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Razorpay connection error: {str(e)}",
        )


@router.post("/create-order", response_model=CreateOrderResponse)
def create_order(payload: CreateOrderRequest, db: Session = Depends(get_db)):
    """Creates a real Razorpay Test Mode order for an APPROVED offer."""
    bargain = db.query(Bargain).filter(Bargain.id == payload.bargain_id).first()
    if not bargain:
        raise HTTPException(status_code=404, detail="Bargain not found")

    offer = db.query(Offer).filter(Offer.id == payload.offer_id).first()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")

    if offer.bargain_id != bargain.id:
        raise HTTPException(status_code=400, detail="Offer does not belong to this bargain")

    if bargain.status != BargainStatus.APPROVED:
        raise HTTPException(
            status_code=400,
            detail=f"Bargain must be in APPROVED status to create order (current: {bargain.status.value})",
        )

    if offer.status != OfferStatus.APPROVED:
        raise HTTPException(
            status_code=400,
            detail=f"Offer must be in APPROVED status to create order (current: {offer.status.value})",
        )

    # Prevent creating duplicate orders for already completed/succeeded deals
    existing_succeeded = (
        db.query(Payment)
        .filter(
            Payment.bargain_id == bargain.id,
            Payment.offer_id == offer.id,
            Payment.status == PaymentStatus.SUCCEEDED,
        )
        .first()
    )
    if existing_succeeded:
        raise HTTPException(status_code=400, detail="Payment has already succeeded for this offer")

    # Payment amount MUST come strictly from the approved Offer in the database
    amount_inr = offer.offered_price
    amount_paise = int(round(amount_inr * 100))
    currency = "INR"

    key_id = os.getenv("RAZORPAY_KEY_ID", "").strip()
    key_secret = os.getenv("RAZORPAY_KEY_SECRET", "").strip()

    if not key_id or not key_secret:
        raise HTTPException(
            status_code=500,
            detail="Razorpay credentials (RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET) must be set in the environment",
        )

    receipt = f"bargain_{bargain.id}_offer_{offer.id}"
    notes = {
        "bargain_id": str(bargain.id),
        "offer_id": str(offer.id),
    }

    # Create real Razorpay order via API
    order_data = create_razorpay_order_api(key_id, key_secret, amount_paise, receipt, notes)
    order_id = order_data["id"]

    payment = Payment(
        bargain_id=bargain.id,
        offer_id=offer.id,
        razorpay_order_id=order_id,
        amount=amount_inr,
        status=PaymentStatus.PENDING,
    )
    db.add(payment)
    db.flush()

    audit = AuditLog(
        bargain_id=bargain.id,
        event="payment_order_created",
        details=(
            f"Razorpay order '{order_id}' created for offer #{offer.id} "
            f"(Amount: ₹{amount_inr:.2f})."
        ),
    )
    db.add(audit)
    db.commit()
    db.refresh(payment)

    return {
        "razorpay_order_id": order_id,
        "amount": amount_paise,
        "amount_inr": amount_inr,
        "currency": currency,
        "key_id": key_id,
        "payment_id": payment.id,
    }


@router.post("/webhook")
async def payment_webhook(request: Request, db: Session = Depends(get_db)):
    """Handles and verifies Razorpay webhook notifications."""
    raw_body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature") or request.headers.get("x-razorpay-signature")

    webhook_secret = os.getenv("RAZORPAY_WEBHOOK_SECRET", "").strip()
    if not webhook_secret:
        raise HTTPException(status_code=500, detail="RAZORPAY_WEBHOOK_SECRET is not configured on server")

    if not signature:
        raise HTTPException(status_code=400, detail="Missing X-Razorpay-Signature header")

    # Verify signature using HMAC-SHA256
    expected_signature = hmac.new(
        webhook_secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, signature):
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    try:
        event_data = json.loads(raw_body.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_type = event_data.get("event")
    event_id = (
        request.headers.get("x-razorpay-event-id")
        or event_data.get("event_id")
        or event_data.get("id")
        or ""
    )

    payload_obj = event_data.get("payload", {})
    payment_entity = payload_obj.get("payment", {}).get("entity", {})
    order_entity = payload_obj.get("order", {}).get("entity", {})

    order_id = payment_entity.get("order_id") or order_entity.get("id")
    payment_id = payment_entity.get("id")

    if not order_id:
        raise HTTPException(status_code=400, detail="Webhook payload missing order_id")

    # Find the corresponding Payment record
    payment = db.query(Payment).filter(Payment.razorpay_order_id == order_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail=f"No payment found matching Razorpay order {order_id}")

    bargain = db.query(Bargain).filter(Bargain.id == payment.bargain_id).first()
    if not bargain:
        raise HTTPException(status_code=404, detail=f"No bargain found for payment #{payment.id}")

    # IDEMPOTENCY CHECK:
    # 1. If event_id was already logged for this bargain, ignore without duplicating
    if event_id:
        existing_audit = (
            db.query(AuditLog)
            .filter(
                AuditLog.bargain_id == bargain.id,
                AuditLog.details.contains(f"Event ID: {event_id}"),
            )
            .first()
        )
        if existing_audit:
            return {
                "status": "ignored",
                "message": f"Webhook event {event_id} already processed (idempotent)",
            }

    # 2. If payment is already succeeded and bargain completed, ignore duplicate success
    if payment.status == PaymentStatus.SUCCEEDED and bargain.status == BargainStatus.COMPLETED:
        return {
            "status": "ignored",
            "message": "Payment and bargain already completed (idempotent)",
        }

    # Handle Payment Success
    if event_type in ("payment.captured", "order.paid", "payment.authorized"):
        payment.status = PaymentStatus.SUCCEEDED
        if payment_id:
            payment.razorpay_payment_id = payment_id
        bargain.status = BargainStatus.COMPLETED

        # 1. payment_verified audit event
        audit_pv = AuditLog(
            bargain_id=bargain.id,
            event="payment_verified",
            details=(
                f"Payment verified via Razorpay webhook. "
                f"Event ID: {event_id} | Order ID: {order_id} | Payment ID: {payment_id} | Amount: ₹{payment.amount:.2f}"
            ),
        )
        db.add(audit_pv)

        # 2. deal_completed audit event
        product_name = bargain.product.name if bargain.product else f"Product #{bargain.product_id}"
        audit_dc = AuditLog(
            bargain_id=bargain.id,
            event="deal_completed",
            details=(
                f"Deal completed for {product_name}. "
                f"Event ID: {event_id} | Order ID: {order_id} | Final Amount: ₹{payment.amount:.2f}"
            ),
        )
        db.add(audit_dc)
        db.commit()

        return {
            "status": "success",
            "message": "Payment verified and deal completed",
            "bargain_id": bargain.id,
            "payment_id": payment.id,
        }

    # Handle Payment Failure
    elif event_type in ("payment.failed",):
        payment.status = PaymentStatus.FAILED
        if payment_id:
            payment.razorpay_payment_id = payment_id

        # Keep Bargain APPROVED and approved Offer APPROVED (do NOT mark COMPLETED)
        audit_pf = AuditLog(
            bargain_id=bargain.id,
            event="payment_failed",
            details=(
                f"Payment failed via Razorpay webhook. "
                f"Event ID: {event_id} | Order ID: {order_id} | Payment ID: {payment_id}"
            ),
        )
        db.add(audit_pf)
        db.commit()

        return {
            "status": "failed",
            "message": "Payment failure recorded",
            "bargain_id": bargain.id,
            "payment_id": payment.id,
        }

    else:
        # Unhandled event types acknowledged without state change
        return {
            "status": "unhandled",
            "message": f"Event type {event_type} ignored",
        }
