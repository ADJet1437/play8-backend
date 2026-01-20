from sqlalchemy.orm import Session
from typing import Optional, Tuple
from src.user.repository import UserRepository
from src.user.db_model import User
from src.user.models import User as UserModel
from src.core.security import create_access_token, get_google_user_info
from src.core.config import ACCESS_TOKEN_EXPIRE_DAYS
from datetime import timedelta

class UserService:
    def __init__(self, db: Session):
        self.repository = UserRepository(db)
        self.db = db
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self.repository.get_by_id(user_id)
    
    async def authenticate_with_google(self, code: str) -> Tuple[User, str]:
        """Authenticate user with Google OAuth code"""
        # Get user info from Google
        google_user_info = await get_google_user_info(code)
        
        email = google_user_info.get("email")
        name = google_user_info.get("name", email.split("@")[0] if email else "User")
        google_id = google_user_info.get("id")
        
        if not email:
            raise ValueError("Email not provided by Google")
        
        # Check if user exists
        user = self.repository.get_by_email_or_google_id(email, google_id)
        
        if not user:
            # Create new user
            user = self.repository.create(email=email, name=name, google_id=google_id)
        else:
            # Update existing user if needed
            self.repository.update(user, name=name, google_id=google_id)
        
        # Create access token
        access_token = create_access_token(data={"sub": user.id})
        
        return user, access_token
    
    def to_pydantic(self, db_user: User) -> UserModel:
        """Convert DB model to Pydantic model"""
        return UserModel(
            id=db_user.id,
            email=db_user.email,
            name=db_user.name
        )

