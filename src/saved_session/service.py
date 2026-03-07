import json

from sqlalchemy.orm import Session

from src.saved_session.db_model import SavedTrainingSession
from src.saved_session.models import SavedSessionResponse
from src.saved_session.repository import SavedSessionRepository


class SavedSessionService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = SavedSessionRepository(db)

    def save_session(
        self, user_id: str, training_plan: dict, drill_cards: list[dict]
    ) -> SavedSessionResponse:
        """Save a training session"""
        # Extract metadata from training plan
        title = training_plan.get("title", "Untitled Session")
        description = training_plan.get("description", "")
        total_duration = training_plan.get("total_duration", "")
        difficulty = training_plan.get("difficulty", "intermediate")

        # Convert to JSON strings
        training_plan_json = json.dumps(training_plan)
        drill_cards_json = json.dumps(drill_cards)

        session = self.repository.create(
            user_id=user_id,
            title=title,
            description=description,
            total_duration=total_duration,
            difficulty=difficulty,
            training_plan_data=training_plan_json,
            drill_cards_data=drill_cards_json,
        )

        return self._to_response(session)

    def get_session(self, session_id: str, user_id: str) -> SavedSessionResponse | None:
        """Get a saved session by ID"""
        session = self.repository.get_by_id(session_id, user_id)
        if not session:
            return None
        return self._to_response(session)

    def list_sessions(
        self, user_id: str, limit: int = 100, offset: int = 0
    ) -> tuple[list[SavedSessionResponse], int]:
        """List all saved sessions for a user"""
        sessions, total = self.repository.list_by_user(user_id, limit, offset)
        return [self._to_response(s) for s in sessions], total

    def delete_session(self, session_id: str, user_id: str) -> bool:
        """Delete a saved session"""
        return self.repository.delete(session_id, user_id)

    def _to_response(self, session: SavedTrainingSession) -> SavedSessionResponse:
        """Convert DB model to response"""
        return SavedSessionResponse(
            id=session.id,
            title=session.title,
            description=session.description,
            total_duration=session.total_duration,
            difficulty=session.difficulty,
            training_plan_data=json.loads(session.training_plan_data),
            drill_cards_data=json.loads(session.drill_cards_data),
            created_at=session.created_at.isoformat(),
            updated_at=session.updated_at.isoformat(),
        )
