from sqlalchemy.orm import Session

from src.machine.db_model import Machine as DBMachine


class MachineRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, machine_id: str) -> DBMachine | None:
        """Get machine by ID"""
        return self.db.query(DBMachine).filter(DBMachine.id == machine_id).first()

    def get_all(self, limit: int = 100, offset: int = 0) -> list[DBMachine]:
        """Get all machines"""
        return self.db.query(DBMachine).offset(offset).limit(limit).all()

    def count_all(self) -> int:
        """Count all machines"""
        return self.db.query(DBMachine).count()

    def create(self, name: str, location: str, status: str = "available") -> DBMachine:
        """Create a new machine"""
        machine = DBMachine(name=name, location=location, status=status)
        self.db.add(machine)
        self.db.commit()
        self.db.refresh(machine)
        return machine

    def update(self, machine: DBMachine, **kwargs) -> DBMachine:
        """Update machine fields"""
        for key, value in kwargs.items():
            if value is not None:
                setattr(machine, key, value)
        self.db.commit()
        self.db.refresh(machine)
        return machine

    def delete(self, machine: DBMachine) -> None:
        """Delete a machine"""
        self.db.delete(machine)
        self.db.commit()

