from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.models import DeleteResponse
from src.core.security import get_current_user
from src.plan.models import PlanItemCreate, PlanItemResponse, PlanProgressUpdate
from src.plan.service import PlanService
from src.user.db_model import User as DBUser

router = APIRouter(prefix="/api/v1/plan", tags=["plan"])


@router.get("/items", response_model=list[PlanItemResponse])
def list_plan_items(
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = PlanService(db)
    return service.get_plan(current_user.id)


@router.post("/items", response_model=PlanItemResponse)
def add_plan_item(
    body: PlanItemCreate,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = PlanService(db)
    return service.add_to_plan(current_user.id, body.model_dump())


@router.put("/items/{item_id}/progress", response_model=PlanItemResponse)
def update_plan_progress(
    item_id: str,
    body: PlanProgressUpdate,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = PlanService(db)
    try:
        return service.update_progress(item_id, current_user.id, body.checked_steps)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/items/{item_id}", response_model=DeleteResponse)
def delete_plan_item(
    item_id: str,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = PlanService(db)
    try:
        service.remove_from_plan(item_id, current_user.id)
        return DeleteResponse(status="success", id=item_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
