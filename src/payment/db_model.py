import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.core.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class Payment(Base):
    __tablename__ = "payments"

    id = Column(String, primary_key=True, default=generate_uuid)
    booking_id = Column(String, ForeignKey("bookings.id"), nullable=False, index=True, unique=True)
    stripe_payment_intent_id = Column(String, nullable=False, index=True, unique=True)
    amount = Column(Integer, nullable=False)  # in öre (1/100 SEK)
    currency = Column(String, nullable=False, default="sek")
    status = Column(String, nullable=False, default="pending")  # pending, succeeded, failed, refunded
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    booking = relationship("Booking", back_populates="payment")
