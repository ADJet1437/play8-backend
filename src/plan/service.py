import json

from sqlalchemy.orm import Session

from src.plan.db_model import PlanItem
from src.plan.models import PlanItemResponse
from src.plan.repository import PlanItemRepository


class PlanService:
    def __init__(self, db: Session):
        self.repo = PlanItemRepository(db)

    def add_to_plan(self, user_id: str, card_data: dict) -> PlanItemResponse:
        item = self.repo.create(user_id, **card_data)
        return self._to_response(item)

    def get_plan(self, user_id: str) -> list[PlanItemResponse]:
        items = self.repo.get_by_user_id(user_id)
        return [self._to_response(item) for item in items]

    def update_progress(
        self, item_id: str, user_id: str, checked_steps: list[bool]
    ) -> PlanItemResponse:
        item = self.repo.get_by_id(item_id)
        if not item or item.user_id != user_id:
            raise ValueError("Plan item not found")
        item = self.repo.update_checked_steps(item, checked_steps)
        return self._to_response(item)

    def remove_from_plan(self, item_id: str, user_id: str) -> None:
        item = self.repo.get_by_id(item_id)
        if not item or item.user_id != user_id:
            raise ValueError("Plan item not found")
        self.repo.delete(item)

    def _to_response(self, item: PlanItem) -> PlanItemResponse:
        return PlanItemResponse(
            id=item.id,
            title=item.title,
            description=item.description,
            category=item.category,
            difficulty=item.difficulty,
            duration=item.duration,
            overview=item.overview,
            steps=json.loads(item.steps),
            tips=json.loads(item.tips),
            checked_steps=json.loads(item.checked_steps),
            status=item.status,
            created_at=item.created_at.isoformat() if item.created_at else "",
            updated_at=item.updated_at.isoformat() if item.updated_at else "",
        )
