import logging
import urllib.parse
from datetime import timedelta

from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Response, status
from sqlalchemy.orm import Session

from src.core.config import ACCESS_TOKEN_EXPIRE_DAYS, GOOGLE_CLIENT_ID, GOOGLE_REDIRECT_URI, IS_PRODUCTION
from src.core.database import get_db
from src.user.models import (
    ForgotPasswordRequest,
    GoogleAuthRequest,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    ResetPasswordRequest,
    Token,
    UserResponse,
    VerifyEmailRequest,
)
from src.user.service import UserService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def _set_auth_cookie(response: Response, access_token: str) -> None:
    expires = timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    response.set_cookie(
        key="token",
        value=access_token,
        httponly=True,
        secure=IS_PRODUCTION,
        samesite="lax",
        max_age=int(expires.total_seconds()),
        path="/",
        domain=None,
    )


# ─── Google OAuth ──────────────────────────────────────────────────────────────

@router.get("/google")
async def google_auth_url():
    """Get Google OAuth URL"""
    try:
        if not GOOGLE_CLIENT_ID:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Google OAuth not configured: GOOGLE_CLIENT_ID is missing",
            )
        if not GOOGLE_REDIRECT_URI:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Google OAuth not configured: GOOGLE_REDIRECT_URI is missing",
            )

        params = {
            "client_id": GOOGLE_CLIENT_ID,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "consent select_account",
        }
        auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
        logger.info("Generated OAuth URL for redirect_uri: %s", GOOGLE_REDIRECT_URI)
        return {"auth_url": auth_url}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error generating Google OAuth URL: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate OAuth URL: {str(e)}",
        ) from e


@router.post("/google/callback", response_model=Token)
async def google_auth_callback(
    auth_request: GoogleAuthRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    """Handle Google OAuth callback — creates or merges user, sets cookie."""
    try:
        logger.info("OAuth callback received with code: %s...", auth_request.code[:10])
        service = UserService(db)
        user, access_token = await service.authenticate_with_google(auth_request.code)
        logger.info("User authenticated: %s", user.email)
        _set_auth_cookie(response, access_token)
        expires = timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
        return Token(access_token=access_token, token_type="bearer", expires_in=int(expires.total_seconds()))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}",
        ) from e


# ─── Email / Password ──────────────────────────────────────────────────────────

@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new account. Sends a verification email."""
    service = UserService(db)
    service.register(email=request.email, password=request.password, name=request.name)
    return MessageResponse(message="Account created. Please check your email to verify your account.")


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(request: VerifyEmailRequest, db: Session = Depends(get_db)):
    """Verify email address using token from email link."""
    service = UserService(db)
    service.verify_email(request.token)
    return MessageResponse(message="Email verified successfully. You can now log in.")


@router.post("/login", response_model=Token)
async def login(request: LoginRequest, response: Response, db: Session = Depends(get_db)):
    """Log in with email and password."""
    service = UserService(db)
    _, access_token = service.login_with_password(request.email, request.password)
    _set_auth_cookie(response, access_token)
    expires = timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    return Token(access_token=access_token, token_type="bearer", expires_in=int(expires.total_seconds()))


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Send password reset email. Always returns 200 to prevent email enumeration."""
    service = UserService(db)
    service.forgot_password(request.email)
    return MessageResponse(message="If an account with that email exists, a reset link has been sent.")


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset password using token from email link."""
    service = UserService(db)
    service.reset_password(request.token, request.new_password)
    return MessageResponse(message="Password reset successfully. You can now log in.")


# ─── Session ───────────────────────────────────────────────────────────────────

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    token: str | None = Cookie(None),
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
):
    """Get current authenticated user info (returns null if not authenticated)."""
    token_value = None
    if token:
        token_value = token
    elif authorization and authorization.startswith("Bearer "):
        token_value = authorization.replace("Bearer ", "")

    if not token_value:
        return UserResponse(user=None)

    from src.core.security import verify_token

    payload = verify_token(token_value)
    if payload is None:
        return UserResponse(user=None)

    user_id: str = payload.get("sub")
    if user_id is None:
        return UserResponse(user=None)

    service = UserService(db)
    user = service.get_user_by_id(user_id)
    if user is None:
        return UserResponse(user=None)

    return UserResponse(user=service.to_pydantic(user))


@router.post("/logout")
async def logout(response: Response):
    """Logout user by clearing cookie."""
    response.delete_cookie(key="token", httponly=True, secure=IS_PRODUCTION, samesite="lax")
    return {"message": "Logged out successfully"}
