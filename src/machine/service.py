from sqlalchemy.orm import Session
from typing import Optional, List
from src.machine.repository import MachineRepository
from src.machine.db_model import Machine as DBMachine
from src.machine.models import Machine as MachineModel, MachineCreate, MachineUpdate

class MachineService:
    def __init__(self, db: Session):
        self.repository = MachineRepository(db)
        self.db = db
    
    def get_all_machines(self, limit: int = 100, offset: int = 0) -> tuple[List[DBMachine], int]:
        """Get all machines"""
        machines = self.repository.get_all(limit, offset)
        total = self.repository.count_all()
        return machines, total
    
    def get_machine_by_id(self, machine_id: str) -> Optional[DBMachine]:
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
    
    def to_pydantic(self, db_machine: DBMachine) -> MachineModel:
        """Convert DB model to Pydantic model"""
        return MachineModel(
            id=db_machine.id,
            name=db_machine.name,
            location=db_machine.location,
            status=db_machine.status
        )


