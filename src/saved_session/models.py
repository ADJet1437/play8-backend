from pydantic import BaseModel


class SavedSessionCreate(BaseModel):
    """Request to save a training session"""

    training_plan_data: dict  # TrainingPlanCard as dict
    drill_cards_data: list[dict]  # DrillCard[] as list of dicts


class SavedSessionResponse(BaseModel):
    """Saved training session response"""

    id: str
    title: str
    description: str
    total_duration: str
    difficulty: str
    training_plan_data: dict
    drill_cards_data: list[dict]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True
