from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from src.booking.repository import BookingRepository
from src.booking.db_model import Booking as DBBooking
from src.booking.models import Booking as BookingModel, BookingCreate, BookingUpdate
from src.machine.repository import MachineRepository

class BookingService:
    def __init__(self, db: Session):
        self.repository = BookingRepository(db)
        self.machine_repository = MachineRepository(db)
        self.db = db
    
    def get_bookings_by_user(
        self,
        user_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[List[DBBooking], int]:
        """Get all bookings for a user"""
        bookings = self.repository.get_by_user_id(user_id, limit, offset)
        total = self.repository.count_by_user_id(user_id)
        return bookings, total
    
    def get_booking_by_id(self, booking_id: str, user_id: str) -> Optional[DBBooking]:
        """Get a specific booking that belongs to a user"""
        return self.repository.get_by_user_and_id(user_id, booking_id)
    
    def create_booking(self, user_id: str, booking_data: BookingCreate) -> DBBooking:
        """Create a new booking"""
        # Verify machine exists
        machine = self.machine_repository.get_by_id(booking_data.machine_id)
        if not machine:
            raise ValueError("Machine not found")
        
        # Parse start_time string to datetime
        start_time = datetime.fromisoformat(booking_data.start_time.replace('Z', '+00:00'))
        end_time = None
        if booking_data.end_time:
            end_time = datetime.fromisoformat(booking_data.end_time.replace('Z', '+00:00'))
        
        # Create booking
        return self.repository.create(
            user_id=user_id,
            machine_id=booking_data.machine_id,
            start_time=start_time,
            end_time=end_time,
            status=booking_data.status
        )
    
    def update_booking(
        self,
        booking_id: str,
        user_id: str,
        booking_update: BookingUpdate
    ) -> DBBooking:
        """Update a booking"""
        booking = self.repository.get_by_user_and_id(user_id, booking_id)
        if not booking:
            raise ValueError("Booking not found")
        
        # Verify machine exists if updating machine_id
        if booking_update.machine_id:
            machine = self.machine_repository.get_by_id(booking_update.machine_id)
            if not machine:
                raise ValueError("Machine not found")
        
        # Prepare update data
        update_data = booking_update.model_dump(exclude_unset=True)
        # Remove user_id from update data (shouldn't be changed)
        update_data.pop("user_id", None)
        
        return self.repository.update(booking, **update_data)
    
    def delete_booking(self, booking_id: str, user_id: str) -> None:
        """Delete a booking"""
        booking = self.repository.get_by_user_and_id(user_id, booking_id)
        if not booking:
            raise ValueError("Booking not found")
        
        self.repository.delete(booking)
    
    def to_pydantic(self, db_booking: DBBooking) -> BookingModel:
        """Convert DB model to Pydantic model"""
        return BookingModel(
            id=db_booking.id,
            user_id=db_booking.user_id,
            machine_id=db_booking.machine_id,
            start_time=db_booking.start_time.isoformat() if db_booking.start_time else "",
            end_time=db_booking.end_time.isoformat() if db_booking.end_time else None,
            status=db_booking.status
        )

