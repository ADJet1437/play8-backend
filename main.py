from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
import uuid

from models import (
    Booking, BookingCreate, BookingUpdate,
    Machine, MachineCreate, MachineUpdate,
    PagedResponse, DeleteResponse
)

app = FastAPI(title="Play8 Court Machine Booking API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage
bookings_db: Dict[str, Booking] = {}
machines_db: Dict[str, Machine] = {}

# Initialize with some sample machines
def init_sample_data():
    sample_machines = [
        Machine(id=str(uuid.uuid4()), name="Court 1", location="Building A", status="available"),
        Machine(id=str(uuid.uuid4()), name="Court 2", location="Building A", status="available"),
        Machine(id=str(uuid.uuid4()), name="Court 3", location="Building B", status="maintenance"),
    ]
    for machine in sample_machines:
        machines_db[machine.id] = machine

init_sample_data()

# Booking endpoints
@app.get("/api/v1/bookings")
def list_bookings(limit: int = 100, offset: int = 0) -> PagedResponse[Booking]:
    bookings_list = list(bookings_db.values())
    total = len(bookings_list)
    paginated = bookings_list[offset:offset + limit]

    return PagedResponse(
        data=paginated,
        total=total,
        limit=limit,
        offset=offset
    )

@app.get("/api/v1/bookings/{booking_id}")
def get_booking(booking_id: str) -> Booking:
    if booking_id not in bookings_db:
        raise HTTPException(status_code=404, detail="Booking not found")
    return bookings_db[booking_id]

@app.post("/api/v1/bookings")
def create_booking(booking: BookingCreate) -> Booking:
    booking_id = str(uuid.uuid4())
    new_booking = Booking(id=booking_id, **booking.model_dump())
    bookings_db[booking_id] = new_booking
    return new_booking

@app.put("/api/v1/bookings/{booking_id}")
def update_booking(booking_id: str, booking_update: BookingUpdate) -> Booking:
    if booking_id not in bookings_db:
        raise HTTPException(status_code=404, detail="Booking not found")

    existing_booking = bookings_db[booking_id]
    update_data = booking_update.model_dump(exclude_unset=True)

    updated_booking = existing_booking.model_copy(update=update_data)
    bookings_db[booking_id] = updated_booking
    return updated_booking

@app.delete("/api/v1/bookings/{booking_id}")
def delete_booking(booking_id: str) -> DeleteResponse:
    if booking_id not in bookings_db:
        raise HTTPException(status_code=404, detail="Booking not found")

    del bookings_db[booking_id]
    return DeleteResponse(status="success", id=booking_id)

# Machine endpoints
@app.get("/api/v1/machines")
def list_machines(limit: int = 100, offset: int = 0) -> PagedResponse[Machine]:
    machines_list = list(machines_db.values())
    total = len(machines_list)
    paginated = machines_list[offset:offset + limit]

    return PagedResponse(
        data=paginated,
        total=total,
        limit=limit,
        offset=offset
    )

@app.get("/api/v1/machines/{machine_id}")
def get_machine(machine_id: str) -> Machine:
    if machine_id not in machines_db:
        raise HTTPException(status_code=404, detail="Machine not found")
    return machines_db[machine_id]

@app.post("/api/v1/machines")
def create_machine(machine: MachineCreate) -> Machine:
    machine_id = str(uuid.uuid4())
    new_machine = Machine(id=machine_id, **machine.model_dump())
    machines_db[machine_id] = new_machine
    return new_machine

@app.put("/api/v1/machines/{machine_id}")
def update_machine(machine_id: str, machine_update: MachineUpdate) -> Machine:
    if machine_id not in machines_db:
        raise HTTPException(status_code=404, detail="Machine not found")

    existing_machine = machines_db[machine_id]
    update_data = machine_update.model_dump(exclude_unset=True)

    updated_machine = existing_machine.model_copy(update=update_data)
    machines_db[machine_id] = updated_machine
    return updated_machine

@app.delete("/api/v1/machines/{machine_id}")
def delete_machine(machine_id: str) -> DeleteResponse:
    if machine_id not in machines_db:
        raise HTTPException(status_code=404, detail="Machine not found")

    del machines_db[machine_id]
    return DeleteResponse(status="success", id=machine_id)

@app.get("/")
def root():
    return {"message": "Play8 Court Machine Booking API", "status": "running"}
