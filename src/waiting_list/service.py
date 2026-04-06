from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.core.email import send_waiting_list_email
from src.waiting_list.repository import WaitingListRepository


class WaitingListService:
    def __init__(self, db: Session):
        self.repository = WaitingListRepository(db)

    def join(self, email: str, plan: str, message: str | None = None) -> None:
        existing = self.repository.get_by_email_and_plan(email, plan)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You're already on the list for this plan.",
            )
        self.repository.create(email=email, plan=plan, message=message)
        send_waiting_list_email(email, plan)
