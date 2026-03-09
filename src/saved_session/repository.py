from sqlalchemy.orm import Session

from src.saved_session.db_model import SavedTrainingSession


class SavedSessionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        user_id: str,
        title: str,
        description: str,
        total_duration: str,
        difficulty: str,
        training_plan_data: str,
        drill_cards_data: str,
    ) -> SavedTrainingSession:
        """Create a new saved training session"""
        session = SavedTrainingSession(
            user_id=user_id,
            title=title,
            description=description,
            total_duration=total_duration,
            difficulty=difficulty,
            training_plan_data=training_plan_data,
            drill_cards_data=drill_cards_data,
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_by_id(self, session_id: str, user_id: str) -> SavedTrainingSession | None:
        """Get a saved session by ID for a specific user"""
        return (
            self.db.query(SavedTrainingSession)
            .filter(
                SavedTrainingSession.id == session_id,
                SavedTrainingSession.user_id == user_id,
            )
            .first()
        )

    def list_by_user(
        self, user_id: str, limit: int = 100, offset: int = 0
    ) -> tuple[list[SavedTrainingSession], int]:
        """List all saved sessions for a user (newest first)"""
        query = (
            self.db.query(SavedTrainingSession)
            .filter(SavedTrainingSession.user_id == user_id)
            .order_by(SavedTrainingSession.created_at.desc())
        )

        total = query.count()
        sessions = query.limit(limit).offset(offset).all()
        return sessions, total

    def update_drill_cards(
        self, session_id: str, user_id: str, drill_cards_data: str
    ) -> SavedTrainingSession | None:
        """Update drill cards data for a saved session"""
        session = self.get_by_id(session_id, user_id)
        if not session:
            return None
        session.drill_cards_data = drill_cards_data
        self.db.commit()
        self.db.refresh(session)
        return session

    def delete(self, session_id: str, user_id: str) -> bool:
        """Delete a saved session"""
        session = self.get_by_id(session_id, user_id)
        if not session:
            return False

        self.db.delete(session)
        self.db.commit()
        return True
