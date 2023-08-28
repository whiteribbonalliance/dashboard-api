from fastapi import Depends, APIRouter, status
from fastapi.security import OAuth2PasswordRequestForm

from app import auth_handler
from app import databases
from app import http_exceptions
from app.schemas.token import Token

router = APIRouter(prefix="/auth")


@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    """Login & access token"""

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

    return Token(access_token=access_token)
