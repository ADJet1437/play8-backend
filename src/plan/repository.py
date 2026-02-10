import json

from sqlalchemy.orm import Session

from src.plan.db_model import PlanItem


class PlanItemRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user_id(self, user_id: str) -> list[PlanItem]:
        return (
            self.db.query(PlanItem)
            .filter(PlanItem.user_id == user_id)
            .order_by(PlanItem.created_at.asc())
            .all()
        )

    def get_by_id(self, item_id: str) -> PlanItem | None:
        return self.db.query(PlanItem).filter(PlanItem.id == item_id).first()

    def create(self, user_id: str, **card_data) -> PlanItem:
        steps = card_data.pop("steps", [])
        tips = card_data.pop("tips", [])
        checked_steps = [False] * len(steps)
        item = PlanItem(
            user_id=user_id,
            steps=json.dumps(steps),
            tips=json.dumps(tips),
            checked_steps=json.dumps(checked_steps),
            **card_data,
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def update_checked_steps(self, item: PlanItem, checked_steps: list[bool]) -> PlanItem:
        steps = json.loads(item.steps)
        all_checked = len(steps) > 0 and all(checked_steps)
        any_checked = any(checked_steps)
        if all_checked:
            status = "complete"
        elif any_checked:
            status = "in_progress"
        else:
            status = "todo"
        item.checked_steps = json.dumps(checked_steps)
        item.status = status
        self.db.commit()
        self.db.refresh(item)
        return item

    def delete(self, item: PlanItem) -> None:
        self.db.delete(item)
        self.db.commit()
