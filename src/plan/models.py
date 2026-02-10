from pydantic import BaseModel


class PlanItemCreate(BaseModel):
    title: str
    description: str = ""
    category: str = "training"
    difficulty: str | None = None
    duration: str | None = None
    overview: str = ""
    steps: list[str] = []
    tips: list[str] = []


class PlanItemResponse(BaseModel):
    id: str
    title: str
    description: str
    category: str
    difficulty: str | None = None
    duration: str | None = None
    overview: str
    steps: list[str]
    tips: list[str]
    checked_steps: list[bool]
    status: str
    created_at: str
    updated_at: str


class PlanProgressUpdate(BaseModel):
    checked_steps: list[bool]
