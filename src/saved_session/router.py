from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.models import DeleteResponse, PagedResponse
from src.core.security import get_current_user
from src.saved_session.models import SavedSessionCreate, SavedSessionResponse
from src.saved_session.service import SavedSessionService
from src.user.db_model import User as DBUser

router = APIRouter(prefix="/api/v1/saved-sessions", tags=["saved-sessions"])


@router.post("", response_model=SavedSessionResponse)
def save_training_session(
    body: SavedSessionCreate,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Save a training session to user's plans"""
    service = SavedSessionService(db)
    return service.save_session(
        user_id=current_user.id,
        training_plan=body.training_plan_data,
        drill_cards=body.drill_cards_data,
    )


@router.get("", response_model=PagedResponse[SavedSessionResponse])
def list_saved_sessions(
    limit: int = 100,
    offset: int = 0,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all saved training sessions (newest first)"""
    service = SavedSessionService(db)
    sessions, total = service.list_sessions(current_user.id, limit, offset)
    return PagedResponse(data=sessions, total=total, limit=limit, offset=offset)


@router.get("/{session_id}", response_model=SavedSessionResponse)
def get_saved_session(
    session_id: str,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a saved training session by ID"""
    service = SavedSessionService(db)
    session = service.get_session(session_id, current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.delete("/{session_id}", response_model=DeleteResponse)
def delete_saved_session(
    session_id: str,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a saved training session"""
    service = SavedSessionService(db)
    success = service.delete_session(session_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return DeleteResponse(status="success", id=session_id)
