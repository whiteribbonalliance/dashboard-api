from fastapi import Depends, APIRouter, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from app import auth_handler
from app import databases
from app import http_exceptions
from app.core.settings import settings

router = APIRouter(prefix="/auth")

DOMAIN = settings.DOMAIN
SECURE_COOKIE = settings.SECURE_COOKIE


@router.post("/login", status_code=status.HTTP_200_OK)
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
        secure=SECURE_COOKIE,
        domain=DOMAIN,
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(response: Response):
    """Logout: Remove access token cookie"""

    response.delete_cookie(
        key="token", httponly=True, secure=SECURE_COOKIE, domain=DOMAIN
    )


@router.get("/check", status_code=status.HTTP_200_OK)
async def check(
    response: Response,
    username: str = Depends(auth_handler.auth_wrapper_access_token),
):
    """Check"""

    if not username:
        response.delete_cookie(
            key="token", httponly=True, secure=SECURE_COOKIE, domain=DOMAIN
        )

        raise http_exceptions.UnauthorizedHTTPException()
