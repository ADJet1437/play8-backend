from typing import Optional

from sqlalchemy.orm import Session

from src.user.db_model import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: str) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def get_by_google_id(self, google_id: str) -> Optional[User]:
        return self.db.query(User).filter(User.google_id == google_id).first()

    def get_by_email_or_google_id(self, email: str, google_id: str) -> Optional[User]:
        return self.db.query(User).filter(
            (User.email == email) | (User.google_id == google_id)
        ).first()

    def create(
        self,
        email: str,
        name: str,
        google_id: Optional[str] = None,
        password_hash: Optional[str] = None,
        is_verified: bool = True,
    ) -> User:
        user = User(
            email=email,
            name=name,
            google_id=google_id,
            password_hash=password_hash,
            is_verified=is_verified,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update(
        self,
        user: User,
        name: Optional[str] = None,
        google_id: Optional[str] = None,
        password_hash: Optional[str] = None,
        is_verified: Optional[bool] = None,
    ) -> User:
        if name is not None:
            user.name = name
        if google_id is not None and not user.google_id:
            user.google_id = google_id
        if password_hash is not None:
            user.password_hash = password_hash
        if is_verified is not None:
            user.is_verified = is_verified
        self.db.commit()
        self.db.refresh(user)
        return user
