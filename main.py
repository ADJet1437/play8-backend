from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from contextlib import asynccontextmanager

from database import get_db, init_database as create_tables
from db_models import Machine as DBMachine, Booking as DBBooking
from models import (
    Booking, BookingCreate, BookingUpdate,
    Machine, MachineCreate, MachineUpdate,
    PagedResponse, DeleteResponse
)

# Lifespan event handler for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize database
    create_tables()
    from init_db import init_sample_data
    init_sample_data()
    yield
    # Shutdown: Add cleanup code here if needed

app = FastAPI(title="Play8 Court Machine Booking API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://play8.ai",
        "https://admin.play8.ai",
        "https://www.play8.ai",
        "http://localhost:3011",
        "http://localhost:5173",  # Vite default dev server
        "http://localhost:3000",  # Common React dev server
        "http://localhost:5174",  # Admin frontend (Vite dev server alternative port)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper functions to convert between DB models and Pydantic models
def db_machine_to_pydantic(db_machine: DBMachine) -> Machine:
    return Machine(
        id=db_machine.id,
        name=db_machine.name,
        location=db_machine.location,
        status=db_machine.status
    )

def db_booking_to_pydantic(db_booking: DBBooking) -> Booking:
    return Booking(
        id=db_booking.id,
        user_id=db_booking.user_id,
        machine_id=db_booking.machine_id,
        start_time=db_booking.start_time.isoformat() if db_booking.start_time else "",
        end_time=db_booking.end_time.isoformat() if db_booking.end_time else None,
        status=db_booking.status
    )

# Booking endpoints
@app.get("/api/v1/bookings", response_model=PagedResponse[Booking])
def list_bookings(limit: int = 100, offset: int = 0, db: Session = Depends(get_db)):
    total = db.query(DBBooking).count()
    bookings = db.query(DBBooking).offset(offset).limit(limit).all()
    
    return PagedResponse(
        data=[db_booking_to_pydantic(b) for b in bookings],
        total=total,
        limit=limit,
        offset=offset
    )

@app.get("/api/v1/bookings/{booking_id}", response_model=Booking)
def get_booking(booking_id: str, db: Session = Depends(get_db)):
    booking = db.query(DBBooking).filter(DBBooking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return db_booking_to_pydantic(booking)

@app.post("/api/v1/bookings", response_model=Booking)
def create_booking(booking: BookingCreate, db: Session = Depends(get_db)):
    # Check if machine exists
    machine = db.query(DBMachine).filter(DBMachine.id == booking.machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    
    # Parse start_time string to datetime
    start_time = datetime.fromisoformat(booking.start_time.replace('Z', '+00:00'))
    
    # Create booking
    db_booking = DBBooking(
        user_id=booking.user_id,
        machine_id=booking.machine_id,
        start_time=start_time,
        end_time=datetime.fromisoformat(booking.end_time.replace('Z', '+00:00')) if booking.end_time else None,
        status=booking.status
    )
    
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    
    return db_booking_to_pydantic(db_booking)

@app.put("/api/v1/bookings/{booking_id}", response_model=Booking)
def update_booking(booking_id: str, booking_update: BookingUpdate, db: Session = Depends(get_db)):
    db_booking = db.query(DBBooking).filter(DBBooking.id == booking_id).first()
    if not db_booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Update fields
    update_data = booking_update.model_dump(exclude_unset=True)
    
    if "start_time" in update_data and update_data["start_time"]:
        db_booking.start_time = datetime.fromisoformat(update_data["start_time"].replace('Z', '+00:00'))
    if "end_time" in update_data and update_data["end_time"]:
        db_booking.end_time = datetime.fromisoformat(update_data["end_time"].replace('Z', '+00:00'))
    if "user_id" in update_data:
        db_booking.user_id = update_data["user_id"]
    if "machine_id" in update_data:
        # Verify machine exists
        machine = db.query(DBMachine).filter(DBMachine.id == update_data["machine_id"]).first()
        if not machine:
            raise HTTPException(status_code=404, detail="Machine not found")
        db_booking.machine_id = update_data["machine_id"]
    if "status" in update_data:
        db_booking.status = update_data["status"]
    
    db.commit()
    db.refresh(db_booking)
    
    return db_booking_to_pydantic(db_booking)

@app.delete("/api/v1/bookings/{booking_id}", response_model=DeleteResponse)
def delete_booking(booking_id: str, db: Session = Depends(get_db)):
    db_booking = db.query(DBBooking).filter(DBBooking.id == booking_id).first()
    if not db_booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    db.delete(db_booking)
    db.commit()
    
    return DeleteResponse(status="success", id=booking_id)

# Machine endpoints
@app.get("/api/v1/machines", response_model=PagedResponse[Machine])
def list_machines(limit: int = 100, offset: int = 0, db: Session = Depends(get_db)):
    total = db.query(DBMachine).count()
    machines = db.query(DBMachine).offset(offset).limit(limit).all()
    
    return PagedResponse(
        data=[db_machine_to_pydantic(m) for m in machines],
        total=total,
        limit=limit,
        offset=offset
    )

@app.get("/api/v1/machines/{machine_id}", response_model=Machine)
def get_machine(machine_id: str, db: Session = Depends(get_db)):
    machine = db.query(DBMachine).filter(DBMachine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    return db_machine_to_pydantic(machine)

@app.post("/api/v1/machines", response_model=Machine)
def create_machine(machine: MachineCreate, db: Session = Depends(get_db)):
    db_machine = DBMachine(
        name=machine.name,
        location=machine.location,
        status=machine.status
    )
    
    db.add(db_machine)
    db.commit()
    db.refresh(db_machine)
    
    return db_machine_to_pydantic(db_machine)

@app.put("/api/v1/machines/{machine_id}", response_model=Machine)
def update_machine(machine_id: str, machine_update: MachineUpdate, db: Session = Depends(get_db)):
    db_machine = db.query(DBMachine).filter(DBMachine.id == machine_id).first()
    if not db_machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    
    update_data = machine_update.model_dump(exclude_unset=True)
    
    if "name" in update_data:
        db_machine.name = update_data["name"]
    if "location" in update_data:
        db_machine.location = update_data["location"]
    if "status" in update_data:
        db_machine.status = update_data["status"]
    
    db.commit()
    db.refresh(db_machine)
    
    return db_machine_to_pydantic(db_machine)

@app.delete("/api/v1/machines/{machine_id}", response_model=DeleteResponse)
def delete_machine(machine_id: str, db: Session = Depends(get_db)):
    db_machine = db.query(DBMachine).filter(DBMachine.id == machine_id).first()
    if not db_machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    
    db.delete(db_machine)
    db.commit()
    
    return DeleteResponse(status="success", id=machine_id)

@app.get("/")
def root():
    return {"message": "Play8 Court Machine Booking API", "status": "running"}
