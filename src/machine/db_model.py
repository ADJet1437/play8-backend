import uuid

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.core.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class Machine(Base):
    __tablename__ = "machines"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    location = Column(String, nullable=False)
    status = Column(
        String, nullable=False, default="available"
    )  # available, maintenance, unavailable
    price_per_hour = Column(Integer, nullable=False, default=12000)  # in öre (1/100 SEK), default 120 SEK
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship
    bookings = relationship("Booking", back_populates="machine")




