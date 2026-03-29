from sqlalchemy.orm import Session

from src.payment.db_model import Payment as DBPayment


class PaymentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, payment_id: str) -> DBPayment | None:
        return self.db.query(DBPayment).filter(DBPayment.id == payment_id).first()

    def get_by_booking_id(self, booking_id: str) -> DBPayment | None:
        return self.db.query(DBPayment).filter(DBPayment.booking_id == booking_id).first()

    def get_by_stripe_intent_id(self, stripe_payment_intent_id: str) -> DBPayment | None:
        return (
            self.db.query(DBPayment)
            .filter(DBPayment.stripe_payment_intent_id == stripe_payment_intent_id)
            .first()
        )

    def create(
        self,
        booking_id: str,
        stripe_payment_intent_id: str,
        amount: int,
        currency: str = "sek",
        status: str = "pending",
    ) -> DBPayment:
        payment = DBPayment(
            booking_id=booking_id,
            stripe_payment_intent_id=stripe_payment_intent_id,
            amount=amount,
            currency=currency,
            status=status,
        )
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        return payment

    def update_status(self, payment: DBPayment, status: str) -> DBPayment:
        payment.status = status
        self.db.commit()
        self.db.refresh(payment)
        return payment
