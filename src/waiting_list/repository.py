from typing import Optional

from sqlalchemy.orm import Session

from src.waiting_list.db_model import WaitingListEntry


class WaitingListRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_email_and_plan(self, email: str, plan: str) -> Optional[WaitingListEntry]:
        return (
            self.db.query(WaitingListEntry)
            .filter(WaitingListEntry.email == email, WaitingListEntry.plan == plan)
            .first()
        )

    def create(self, email: str, plan: str, message: str | None = None) -> WaitingListEntry:
        entry = WaitingListEntry(email=email, plan=plan, message=message)
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry
