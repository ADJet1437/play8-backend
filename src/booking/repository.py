from datetime import datetime

from sqlalchemy.orm import Session

from src.booking.db_model import Booking as DBBooking


class BookingRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, booking_id: str) -> DBBooking | None:
        """Get booking by ID"""
        return self.db.query(DBBooking).filter(DBBooking.id == booking_id).first()

    def get_by_user_id(self, user_id: str, limit: int = 100, offset: int = 0) -> list[DBBooking]:
        """Get all bookings for a user"""
        return (
            self.db.query(DBBooking)
            .filter(DBBooking.user_id == user_id)
            .offset(offset)
            .limit(limit)
            .all()
        )

    def count_by_user_id(self, user_id: str) -> int:
        """Count bookings for a user"""
        return self.db.query(DBBooking).filter(DBBooking.user_id == user_id).count()

    def get_by_user_and_id(self, user_id: str, booking_id: str) -> DBBooking | None:
        """Get booking by ID that belongs to a specific user"""
        return (
            self.db.query(DBBooking)
            .filter(DBBooking.id == booking_id, DBBooking.user_id == user_id)
            .first()
        )

    def create(
        self,
        user_id: str,
        machine_id: str,
        start_time: datetime,
        end_time: datetime | None = None,
        status: str = "active",
    ) -> DBBooking:
        """Create a new booking"""
        booking = DBBooking(
            user_id=user_id,
            machine_id=machine_id,
            start_time=start_time,
            end_time=end_time,
            status=status,
        )
        self.db.add(booking)
        self.db.commit()
        self.db.refresh(booking)
        return booking

    def update(self, booking: DBBooking, **kwargs) -> DBBooking:
        """Update booking fields"""
        for key, value in kwargs.items():
            if value is not None:
                if key == "start_time" or key == "end_time":
                    # Parse ISO string to datetime
                    if isinstance(value, str):
                        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
                setattr(booking, key, value)
        self.db.commit()
        self.db.refresh(booking)
        return booking

    def delete(self, booking: DBBooking) -> None:
        """Delete a booking"""
        self.db.delete(booking)
        self.db.commit()
