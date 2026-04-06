from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.waiting_list.models import WaitingListRequest, WaitingListResponse
from src.waiting_list.service import WaitingListService

router = APIRouter(prefix="/api/v1/waiting-list", tags=["waiting-list"])


@router.post("", response_model=WaitingListResponse, status_code=status.HTTP_201_CREATED)
def join_waiting_list(request: WaitingListRequest, db: Session = Depends(get_db)):
    """Join the rental waiting list. No authentication required."""
    service = WaitingListService(db)
    service.join(email=request.email, plan=request.plan, message=request.message)
    return WaitingListResponse(message="You're on the list! We'll be in touch.")
