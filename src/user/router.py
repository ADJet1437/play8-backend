from datetime import timedelta

from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Response, status
from sqlalchemy.orm import Session

from src.core.config import ACCESS_TOKEN_EXPIRE_DAYS, GOOGLE_CLIENT_ID, IS_PRODUCTION
from src.core.database import get_db
from src.user.models import GoogleAuthRequest, Token, UserResponse
from src.user.service import UserService

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

@router.get("/google")
async def google_auth_url():
    """Get Google OAuth URL"""
    import logging
    import urllib.parse

    logger = logging.getLogger(__name__)

    try:
        if not GOOGLE_CLIENT_ID:
            logger.error("GOOGLE_CLIENT_ID is not configured")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Google OAuth not configured: GOOGLE_CLIENT_ID is missing"
            )

        from src.core.config import GOOGLE_REDIRECT_URI

        if not GOOGLE_REDIRECT_URI:
            logger.error("GOOGLE_REDIRECT_URI is not configured")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Google OAuth not configured: GOOGLE_REDIRECT_URI is missing"
            )

        # Build OAuth URL with proper encoding
        params = {
            "client_id": GOOGLE_CLIENT_ID,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "consent select_account",  # Force consent screen and account selection
        }

        auth_url = (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"{urllib.parse.urlencode(params)}"
        )

        logger.info(f"Generated OAuth URL for redirect_uri: {GOOGLE_REDIRECT_URI}")
        return {"auth_url": auth_url}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error generating Google OAuth URL: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate OAuth URL: {str(e)}"
        ) from e

@router.post("/google/callback", response_model=Token)
async def google_auth_callback(
    auth_request: GoogleAuthRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """Handle Google OAuth callback and create/login user"""
    import logging
    logger = logging.getLogger(__name__)

    try:
        logger.info(f"OAuth callback received with code: {auth_request.code[:10]}...")
        service = UserService(db)
        user, access_token = await service.authenticate_with_google(auth_request.code)
        logger.info(f"User authenticated: {user.email}")

        # Set token in HTTP-only cookie (1 week expiry)
        expires = timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
        response.set_cookie(
            key="token",
            value=access_token,
            httponly=True,
            secure=IS_PRODUCTION,
            samesite="lax",
            max_age=int(expires.total_seconds()),
            path="/",
            domain=None
        )

        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=int(expires.total_seconds())
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}"
        ) from e

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    token: str | None = Cookie(None),
    authorization: str | None = Header(None),
    db: Session = Depends(get_db)
):
    """Get current authenticated user info (returns null if not authenticated)"""
    # Try to get token from cookie first, then from Authorization header
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
    """Logout user by clearing cookie"""
    response.delete_cookie(
        key="token",
        httponly=True,
        secure=IS_PRODUCTION,
        samesite="lax"
    )
    return {"message": "Logged out successfully"}


