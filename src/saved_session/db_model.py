import uuid

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from src.core.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class SavedTrainingSession(Base):
    """Saved training session with full plan and drill cards"""

    __tablename__ = "saved_training_sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    total_duration: Mapped[str] = mapped_column(String, nullable=False)
    difficulty: Mapped[str] = mapped_column(String, nullable=False)

    # Store full training plan and drill cards as JSON
    training_plan_data: Mapped[str] = mapped_column(
        Text, nullable=False
    )  # JSON string of TrainingPlanCard
    drill_cards_data: Mapped[str] = mapped_column(
        Text, nullable=False
    )  # JSON string of DrillCard[]

    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
