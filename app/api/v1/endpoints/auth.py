"""
MIT License

Copyright (c) 2023 White Ribbon Alliance. Maintainers: Thomas Wood, https://fastdatascience.com, Zairon Jacobs, https://zaironjacobs.com.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

"""

import json

from fastapi import Depends, APIRouter, status
from fastapi.security import OAuth2PasswordRequestForm

from app import auth_handler, constants
from app import databases
from app import http_exceptions
from app.api import dependencies
from app.core.settings import get_settings
from app.schemas.token import Token
from app.schemas.user import UserBase

settings = get_settings()

router = APIRouter(prefix="/auth")


@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    """Login: Return access token cookie"""

    form_username = form_data.username
    form_password = form_data.password

    if not form_password:
        raise http_exceptions.UnauthorizedHTTPException("Login failed")

    # Check if user exists
    users = databases.get_users_from_databases()
    db_user = users.get(form_username)
    if not db_user:
        raise http_exceptions.UnauthorizedHTTPException("Login failed")

    # Verify password
    if form_password != db_user.password:
        raise http_exceptions.UnauthorizedHTTPException("Login failed")

    # User
    user = UserBase(
        username=db_user.username,
        campaign_access=db_user.campaign_access,
        is_admin=db_user.is_admin,
    )

    # Create access token
    access_token = auth_handler.create_access_token(
        data={"sub": db_user.username, "user": json.loads(user.json())}
    )

    # Max age of cookie (in seconds)
    max_age = (constants.ACCESS_TOKEN_EXPIRE_DAYS * 86400) - 3600

    return Token(access_token=access_token, max_age=max_age)


@router.post("/check", status_code=status.HTTP_200_OK)
async def check(
    username: str = Depends(dependencies.verify_user),
):
    """Check: Verify user"""

    users = databases.get_users_from_databases()
    db_user = users.get(username)
    if not db_user:
        raise http_exceptions.UnauthorizedHTTPException("Unauthorized")
