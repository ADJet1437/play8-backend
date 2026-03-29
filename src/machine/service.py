import datetime as dt

from sqlalchemy.orm import Session

from src.booking.repository import BookingRepository
from src.machine.db_model import Machine as DBMachine
from src.machine.models import Machine as MachineModel
from src.machine.models import MachineCreate, MachineUpdate, SlotInfo, SlotsResponse

OPERATING_HOURS_START = 7   # 07:00
OPERATING_HOURS_END = 22    # last slot is 21:00–22:00, so end_hour = 22

class MachineService:
    def __init__(self, db: Session):
        from src.machine.repository import MachineRepository
        self.repository = MachineRepository(db)
        self.booking_repository = BookingRepository(db)
        self.db = db

    def get_all_machines(self, limit: int = 100, offset: int = 0) -> tuple[list[DBMachine], int]:
        """Get all machines"""
        machines = self.repository.get_all(limit, offset)
        total = self.repository.count_all()
        return machines, total

    def get_machine_by_id(self, machine_id: str) -> DBMachine | None:
        """Get machine by ID"""
        return self.repository.get_by_id(machine_id)

    def create_machine(self, machine_data: MachineCreate) -> DBMachine:
        """Create a new machine"""
        return self.repository.create(
            name=machine_data.name,
            location=machine_data.location,
            status=machine_data.status
        )

    def update_machine(self, machine_id: str, machine_update: MachineUpdate) -> DBMachine:
        """Update a machine"""
        machine = self.repository.get_by_id(machine_id)
        if not machine:
            raise ValueError("Machine not found")

        update_data = machine_update.model_dump(exclude_unset=True)
        return self.repository.update(machine, **update_data)

    def delete_machine(self, machine_id: str) -> None:
        """Delete a machine"""
        machine = self.repository.get_by_id(machine_id)
        if not machine:
            raise ValueError("Machine not found")

        self.repository.delete(machine)

    def get_slots_for_date(self, machine_id: str, date: dt.date) -> SlotsResponse:
        """Return slot availability for a machine on a given date (hours 7–21 inclusive)."""
        booked_hours = self.booking_repository.get_booked_hours_for_date(machine_id, date)
        booked_set = set(booked_hours)

        slots = [
            SlotInfo(
                hour=h,
                status="booked" if h in booked_set else "available",
            )
            for h in range(OPERATING_HOURS_START, OPERATING_HOURS_END)
        ]
        return SlotsResponse(date=date.isoformat(), machine_id=machine_id, slots=slots)

    def to_pydantic(self, db_machine: DBMachine) -> MachineModel:
        """Convert DB model to Pydantic model"""
        return MachineModel(
            id=db_machine.id,
            name=db_machine.name,
            location=db_machine.location,
            status=db_machine.status
        )





