from sqlalchemy.orm import Session
from typing import Optional
from src.user.db_model import User

class UserRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_by_google_id(self, google_id: str) -> Optional[User]:
        """Get user by Google ID"""
        return self.db.query(User).filter(User.google_id == google_id).first()
    
    def get_by_email_or_google_id(self, email: str, google_id: str) -> Optional[User]:
        """Get user by email or Google ID"""
        return self.db.query(User).filter(
            (User.email == email) | (User.google_id == google_id)
        ).first()
    
    def create(self, email: str, name: str, google_id: Optional[str] = None) -> User:
        """Create a new user"""
        user = User(
            email=email,
            name=name,
            google_id=google_id
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def update(self, user: User, name: Optional[str] = None, google_id: Optional[str] = None) -> User:
        """Update user information"""
        if name is not None:
            user.name = name
        if google_id is not None and not user.google_id:
            user.google_id = google_id
        self.db.commit()
        self.db.refresh(user)
        return user

