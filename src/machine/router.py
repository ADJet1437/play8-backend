from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.models import DeleteResponse, PagedResponse
from src.machine.models import Machine, MachineCreate, MachineUpdate
from src.machine.service import MachineService

router = APIRouter(prefix="/api/v1/machines", tags=["machines"])


@router.get("", response_model=PagedResponse[Machine])
def list_machines(limit: int = 100, offset: int = 0, db: Session = Depends(get_db)):
    """List all machines"""
    service = MachineService(db)
    machines, total = service.get_all_machines(limit, offset)

    return PagedResponse(
        data=[service.to_pydantic(m) for m in machines], total=total, limit=limit, offset=offset
    )


@router.get("/{machine_id}", response_model=Machine)
def get_machine(machine_id: str, db: Session = Depends(get_db)):
    """Get a specific machine"""
    service = MachineService(db)
    machine = service.get_machine_by_id(machine_id)

    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")

    return service.to_pydantic(machine)


@router.post("", response_model=Machine)
def create_machine(machine: MachineCreate, db: Session = Depends(get_db)):
    """Create a new machine"""
    service = MachineService(db)
    db_machine = service.create_machine(machine)
    return service.to_pydantic(db_machine)


@router.put("/{machine_id}", response_model=Machine)
def update_machine(machine_id: str, machine_update: MachineUpdate, db: Session = Depends(get_db)):
    """Update a machine"""
    service = MachineService(db)
    try:
        db_machine = service.update_machine(machine_id, machine_update)
        return service.to_pydantic(db_machine)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{machine_id}", response_model=DeleteResponse)
def delete_machine(machine_id: str, db: Session = Depends(get_db)):
    """Delete a machine"""
    service = MachineService(db)
    try:
        service.delete_machine(machine_id)
        return DeleteResponse(status="success", id=machine_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
