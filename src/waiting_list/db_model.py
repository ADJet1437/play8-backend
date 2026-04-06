import uuid

from sqlalchemy import Column, DateTime, String, UniqueConstraint
from sqlalchemy.sql import func

from src.core.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class WaitingListEntry(Base):
    __tablename__ = "waiting_list"

    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, nullable=False, index=True)
    plan = Column(String, nullable=False)  # "week" | "month"
    message = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("email", "plan", name="uq_waiting_list_email_plan"),
    )
