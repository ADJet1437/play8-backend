import datetime as dt

from sqlalchemy.orm import Session

from src.booking.db_model import Booking as DBBooking


class BookingRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, booking_id: str) -> DBBooking | None:
        """Get booking by ID"""
        return self.db.query(DBBooking).filter(DBBooking.id == booking_id).first()

    def get_by_user_id(
        self,
        user_id: str,
        limit: int = 100,
        offset: int = 0,
        statuses: list[str] | None = None,
    ) -> list[DBBooking]:
        """Get bookings for a user, optionally filtered by status list. Only returns future/ongoing bookings."""
        now = dt.datetime.now(tz=dt.UTC)
        query = self.db.query(DBBooking).filter(DBBooking.user_id == user_id, DBBooking.end_time > now)
        if statuses:
            query = query.filter(DBBooking.status.in_(statuses))
        return query.order_by(DBBooking.start_time.asc()).offset(offset).limit(limit).all()

    def count_by_user_id(self, user_id: str, statuses: list[str] | None = None) -> int:
        """Count bookings for a user, optionally filtered by status list. Only counts future/ongoing bookings."""
        now = dt.datetime.now(tz=dt.UTC)
        query = self.db.query(DBBooking).filter(DBBooking.user_id == user_id, DBBooking.end_time > now)
        if statuses:
            query = query.filter(DBBooking.status.in_(statuses))
        return query.count()

    def get_by_user_and_id(self, user_id: str, booking_id: str) -> DBBooking | None:
        """Get booking by ID that belongs to a specific user"""
        return (
            self.db.query(DBBooking)
            .filter(DBBooking.id == booking_id, DBBooking.user_id == user_id)
            .first()
        )

    def get_booked_hours_for_date(self, machine_id: str, date: dt.date) -> list[int]:
        """Return a sorted list of booked hours (0-23) for a machine on a given UTC date."""
        day_start = dt.datetime(date.year, date.month, date.day, tzinfo=dt.UTC)
        day_end = day_start + dt.timedelta(days=1)

        bookings = (
            self.db.query(DBBooking)
            .filter(
                DBBooking.machine_id == machine_id,
                DBBooking.status.in_(["confirmed", "active", "pending"]),
                DBBooking.start_time < day_end,
                DBBooking.end_time > day_start,
            )
            .all()
        )

        booked: set[int] = set()
        for booking in bookings:
            start_h = booking.start_time.hour
            end_h = booking.end_time.hour
            for h in range(start_h, end_h):
                booked.add(h)
        return sorted(booked)

    def has_conflict(self, machine_id: str, start_time: dt.datetime, end_time: dt.datetime, exclude_booking_id: str | None = None) -> bool:
        """Return True if any confirmed/active/pending booking overlaps the given window."""
        query = self.db.query(DBBooking).filter(
            DBBooking.machine_id == machine_id,
            DBBooking.status.in_(["confirmed", "active", "pending"]),
            DBBooking.start_time < end_time,
            DBBooking.end_time > start_time,
        )
        if exclude_booking_id:
            query = query.filter(DBBooking.id != exclude_booking_id)
        return query.first() is not None

    def create(
        self,
        user_id: str,
        machine_id: str,
        start_time: dt.datetime,
        end_time: dt.datetime | None = None,
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
                        value = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
                setattr(booking, key, value)
        self.db.commit()
        self.db.refresh(booking)
        return booking

    def delete(self, booking: DBBooking) -> None:
        """Delete a booking"""
        self.db.delete(booking)
        self.db.commit()

