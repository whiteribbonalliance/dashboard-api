from fastapi import Depends, APIRouter, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from app import auth_handler
from app import databases
from app import http_exceptions
from app.core.settings import settings
from app.schemas.user import UserResponse

router = APIRouter(prefix="/auth")


@router.post("/login", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    """Login: Set access token cookie"""

    form_username = form_data.username
    form_password = form_data.password

    # Check if user exists
    users = databases.get_users()
    db_user = users.get(form_username)
    if not db_user:
        raise http_exceptions.UnauthorizedHTTPException("Login failed")

    # Verify password
    if form_password != db_user.password:
        raise http_exceptions.UnauthorizedHTTPException("Login failed")

    # Create access token
    access_token = auth_handler.create_access_token(data={"sub": db_user.username})

    # Set access token as HttpOnly cookie
    response.set_cookie(
        key="token",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=settings.COOKIE_SECURE,
        domain=settings.COOKIE_DOMAIN,
        samesite=settings.COOKIE_SAMESITE,
    )

    return UserResponse(
        username=db_user.username, campaign_access=db_user.campaign_access
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(response: Response):
    """Logout: Remove access token cookie"""

    response.delete_cookie(
        key="token",
        httponly=True,
        secure=settings.COOKIE_SECURE,
        domain=settings.COOKIE_DOMAIN,
        samesite=settings.COOKIE_SAMESITE,
    )


@router.post("/check", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def check(
    username: str = Depends(auth_handler.auth_wrapper_access_token),
):
    """Check: Verify user"""

    users = databases.get_users()
    db_user = users.get(username)
    if not db_user:
        raise http_exceptions.UnauthorizedHTTPException("Unauthorized")

    return UserResponse(
        username=db_user.username, campaign_access=db_user.campaign_access
    )
