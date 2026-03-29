import math
from datetime import UTC, datetime, timedelta

import stripe
from sqlalchemy.orm import Session

from src.booking.repository import BookingRepository
from src.booking.service import BookingService
from src.core import config
from src.machine.repository import MachineRepository
from src.payment.models import PaymentIntentResponse, RefundResponse
from src.payment.repository import PaymentRepository

stripe.api_key = config.STRIPE_SECRET_KEY


class PaymentService:
    def __init__(self, db: Session):
        self.db = db
        self.payment_repo = PaymentRepository(db)
        self.booking_repo = BookingRepository(db)
        self.machine_repo = MachineRepository(db)

    def calculate_amount(self, price_per_hour: int, start_time: datetime, end_time: datetime) -> int:
        """Calculate total amount in öre. Rounds up to nearest half-hour."""
        duration_seconds = (end_time - start_time).total_seconds()
        duration_hours = duration_seconds / 3600
        # Round up to nearest 0.5 hour increment
        rounded_hours = math.ceil(duration_hours * 2) / 2
        return int(rounded_hours * price_per_hour)

    def create_payment_intent(
        self, user_id: str, machine_id: str, start_time_str: str, end_time_str: str
    ) -> PaymentIntentResponse:
        """Create a booking and a Stripe PaymentIntent together."""
        machine = self.machine_repo.get_by_id(machine_id)
        if not machine:
            raise ValueError("Machine not found")

        start_time = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
        end_time = datetime.fromisoformat(end_time_str.replace("Z", "+00:00"))

        if end_time <= start_time:
            raise ValueError("End time must be after start time")

        if self.booking_repo.has_conflict(machine_id, start_time, end_time):
            raise ValueError("One or more of the selected slots are already booked")

        amount = self.calculate_amount(machine.price_per_hour, start_time, end_time)

        # Create booking with pending status
        booking = self.booking_repo.create(
            user_id=user_id,
            machine_id=machine_id,
            start_time=start_time,
            end_time=end_time,
            status="pending",
        )
        # Mark payment as unpaid
        booking.payment_status = "unpaid"
        self.db.commit()
        self.db.refresh(booking)

        # Create Stripe PaymentIntent
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency="sek",
            metadata={"booking_id": booking.id, "user_id": user_id},
        )

        # Persist payment record
        self.payment_repo.create(
            booking_id=booking.id,
            stripe_payment_intent_id=intent.id,
            amount=amount,
            currency="sek",
            status="pending",
        )

        return PaymentIntentResponse(
            booking_id=booking.id,
            client_secret=intent.client_secret,
            amount=amount,
            amount_sek=amount / 100,
        )

    def handle_webhook(self, payload: bytes, sig_header: str) -> None:
        """Process a Stripe webhook event."""
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, config.STRIPE_WEBHOOK_SECRET)
        except stripe.error.SignatureVerificationError as e:
            raise ValueError(f"Invalid webhook signature: {e}") from e

        if event["type"] == "payment_intent.succeeded":
            intent = event["data"]["object"]
            self._on_payment_succeeded(intent["id"])
        elif event["type"] == "payment_intent.payment_failed":
            intent = event["data"]["object"]
            self._on_payment_failed(intent["id"])

    def _on_payment_succeeded(self, stripe_intent_id: str) -> None:
        payment = self.payment_repo.get_by_stripe_intent_id(stripe_intent_id)
        if not payment:
            return
        self.payment_repo.update_status(payment, "succeeded")

        booking = self.booking_repo.get_by_id(payment.booking_id)
        if booking:
            booking.status = "confirmed"
            booking.payment_status = "paid"
            self.db.commit()

    def _on_payment_failed(self, stripe_intent_id: str) -> None:
        payment = self.payment_repo.get_by_stripe_intent_id(stripe_intent_id)
        if not payment:
            return
        self.payment_repo.update_status(payment, "failed")

        booking = self.booking_repo.get_by_id(payment.booking_id)
        if booking:
            booking.status = "cancelled"
            booking.payment_status = "unpaid"
            self.db.commit()

    def verify_and_confirm(self, stripe_payment_intent_id: str, user_id: str):
        """Called by the client after stripe.confirmCardPayment succeeds.
        Retrieves the PaymentIntent directly from Stripe and confirms the booking
        immediately, without waiting for the webhook."""
        intent = stripe.PaymentIntent.retrieve(stripe_payment_intent_id)
        if intent.status == "succeeded":
            self._on_payment_succeeded(stripe_payment_intent_id)

        payment = self.payment_repo.get_by_stripe_intent_id(stripe_payment_intent_id)
        if not payment:
            raise ValueError("Payment record not found")

        booking = self.booking_repo.get_by_id(payment.booking_id)
        if not booking or booking.user_id != user_id:
            raise ValueError("Booking not found")

        return BookingService(self.db).to_pydantic(booking)

    def refund(self, booking_id: str, user_id: str) -> RefundResponse:
        """Refund a booking if it's more than 24 hours before start time."""
        booking = self.booking_repo.get_by_user_and_id(user_id, booking_id)
        if not booking:
            raise ValueError("Booking not found")

        if booking.payment_status != "paid":
            raise ValueError("Booking has not been paid")

        now = datetime.now(UTC)
        if booking.start_time.tzinfo is None:
            start = booking.start_time.replace(tzinfo=UTC)
        else:
            start = booking.start_time

        if start - now < timedelta(hours=24):
            raise ValueError("Refunds are only allowed more than 24 hours before the booking start time")

        payment = self.payment_repo.get_by_booking_id(booking_id)
        if not payment:
            raise ValueError("Payment record not found")

        stripe.Refund.create(payment_intent=payment.stripe_payment_intent_id)

        self.payment_repo.update_status(payment, "refunded")
        booking.status = "cancelled"
        booking.payment_status = "refunded"
        self.db.commit()

        return RefundResponse(
            booking_id=booking_id,
            status="refunded",
            message="Refund processed successfully",
        )
