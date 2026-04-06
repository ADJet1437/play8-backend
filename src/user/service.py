from datetime import timedelta
from typing import Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.core.config import ACCESS_TOKEN_EXPIRE_DAYS
from src.core.email import send_password_reset_email, send_verification_email, send_welcome_email
from src.core.security import (
    create_access_token,
    create_short_lived_token,
    get_google_user_info,
    hash_password,
    verify_password,
    verify_short_lived_token,
)
from src.user.db_model import User
from src.user.models import User as UserModel
from src.user.repository import UserRepository


class UserService:
    def __init__(self, db: Session):
        self.repository = UserRepository(db)
        self.db = db

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        return self.repository.get_by_id(user_id)

    # ─── Google OAuth ──────────────────────────────────────────────────────────

    async def authenticate_with_google(self, code: str) -> Tuple[User, str]:
        google_user_info = await get_google_user_info(code)

        email = google_user_info.get("email")
        name = google_user_info.get("name", email.split("@")[0] if email else "User")
        google_id = google_user_info.get("id")

        if not email:
            raise ValueError("Email not provided by Google")

        user = self.repository.get_by_email_or_google_id(email, google_id)

        if not user:
            user = self.repository.create(
                email=email, name=name, google_id=google_id, is_verified=True
            )
            send_welcome_email(email, name)
        else:
            # Merge: link google_id and mark verified (Google proves email ownership)
            self.repository.update(user, name=name, google_id=google_id, is_verified=True)

        access_token = create_access_token(data={"sub": user.id})
        return user, access_token

    # ─── Email / Password ──────────────────────────────────────────────────────

    def register(self, email: str, password: str, name: Optional[str]) -> None:
        existing = self.repository.get_by_email(email)
        if existing:
            # Don't leak whether the email exists; just raise a generic error
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists.",
            )

        display_name = name or email.split("@")[0]
        pw_hash = hash_password(password)
        user = self.repository.create(
            email=email,
            name=display_name,
            password_hash=pw_hash,
            is_verified=False,
        )

        token = create_short_lived_token(
            {"sub": user.id, "purpose": "email_verify"},
            timedelta(hours=24),
        )
        send_verification_email(email, display_name, token)

    def verify_email(self, token: str) -> User:
        payload = verify_short_lived_token(token, "email_verify")
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification link.",
            )
        user = self.repository.get_by_id(payload["sub"])
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        if not user.is_verified:
            self.repository.update(user, is_verified=True)
            send_welcome_email(user.email, user.name)
        return user

    def login_with_password(self, email: str, password: str) -> Tuple[User, str]:
        user = self.repository.get_by_email(email)
        if not user or not user.password_hash:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )
        if not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )
        if not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Please verify your email before logging in.",
            )
        access_token = create_access_token(data={"sub": user.id})
        return user, access_token

    def forgot_password(self, email: str) -> None:
        user = self.repository.get_by_email(email)
        # Always return success to avoid email enumeration
        if not user or not user.password_hash:
            return
        token = create_short_lived_token(
            {"sub": user.id, "purpose": "password_reset"},
            timedelta(hours=1),
        )
        send_password_reset_email(email, user.name, token)

    def reset_password(self, token: str, new_password: str) -> None:
        payload = verify_short_lived_token(token, "password_reset")
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset link.",
            )
        user = self.repository.get_by_id(payload["sub"])
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        self.repository.update(user, password_hash=hash_password(new_password))

    def to_pydantic(self, db_user: User) -> UserModel:
        return UserModel(
            id=db_user.id,
            email=db_user.email,
            name=db_user.name,
            is_verified=db_user.is_verified,
        )
