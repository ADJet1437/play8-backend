from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.security import get_current_user
from src.core.models import PagedResponse, DeleteResponse
from src.user.db_model import User as DBUser
from src.booking.models import Booking, BookingCreate, BookingUpdate
from src.booking.service import BookingService

router = APIRouter(prefix="/api/v1/bookings", tags=["bookings"])

@router.get("", response_model=PagedResponse[Booking])
def list_bookings(
    limit: int = 100,
    offset: int = 0,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all bookings for the current user"""
    service = BookingService(db)
    bookings, total = service.get_bookings_by_user(current_user.id, limit, offset)
    
    return PagedResponse(
        data=[service.to_pydantic(b) for b in bookings],
        total=total,
        limit=limit,
        offset=offset
    )

@router.get("/{booking_id}", response_model=Booking)
def get_booking(
    booking_id: str,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific booking"""
    service = BookingService(db)
    booking = service.get_booking_by_id(booking_id, current_user.id)
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    return service.to_pydantic(booking)

@router.post("", response_model=Booking)
def create_booking(
    booking: BookingCreate,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new booking"""
    service = BookingService(db)
    try:
        db_booking = service.create_booking(current_user.id, booking)
        return service.to_pydantic(db_booking)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/{booking_id}", response_model=Booking)
def update_booking(
    booking_id: str,
    booking_update: BookingUpdate,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a booking"""
    service = BookingService(db)
    try:
        db_booking = service.update_booking(booking_id, current_user.id, booking_update)
        return service.to_pydantic(db_booking)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{booking_id}", response_model=DeleteResponse)
def delete_booking(
    booking_id: str,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a booking"""
    service = BookingService(db)
    try:
        service.delete_booking(booking_id, current_user.id)
        return DeleteResponse(status="success", id=booking_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

