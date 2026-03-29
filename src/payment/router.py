from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from src.booking.models import Booking as BookingResponse
from src.core.database import get_db
from src.core.security import get_current_user
from src.payment.models import (
    CreatePaymentIntentRequest,
    PaymentIntentResponse,
    RefundResponse,
    VerifyPaymentRequest,
)
from src.payment.service import PaymentService
from src.user.db_model import User as DBUser

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])


@router.post("/create-intent", response_model=PaymentIntentResponse)
def create_payment_intent(
    request: CreatePaymentIntentRequest,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a booking and a Stripe PaymentIntent. Returns a client_secret for frontend confirmation."""
    service = PaymentService(db)
    try:
        return service.create_payment_intent(
            user_id=current_user.id,
            machine_id=request.machine_id,
            start_time_str=request.start_time,
            end_time_str=request.end_time,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/verify", response_model=BookingResponse)
def verify_payment(
    body: VerifyPaymentRequest,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Called by the client after stripe.confirmCardPayment succeeds.
    Immediately confirms the booking without waiting for the webhook."""
    service = PaymentService(db)
    try:
        return service.verify_and_confirm(body.payment_intent_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Stripe webhook endpoint — no auth, signature verified internally."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    service = PaymentService(db)
    try:
        service.handle_webhook(payload, sig_header)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"status": "ok"}


@router.post("/{booking_id}/refund", response_model=RefundResponse)
def refund_booking(
    booking_id: str,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Refund a booking. Only allowed more than 24 hours before start time."""
    service = PaymentService(db)
    try:
        return service.refund(booking_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
