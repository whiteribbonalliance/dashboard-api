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

from datetime import datetime, timedelta

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

# from app.oauth2_password_bearer_with_cookie import OAuth2PasswordBearerWithCookie
from app import env
from app import http_exceptions, constants

ALGORITHM = "HS256"

oauth2_scheme_access = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def create_access_token(data: dict) -> str:
    """
    Create access token

    :param data: The data to encode the JWT with
    :return: The access token
    """

    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=constants.ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    issued_at = datetime.utcnow()
    to_encode.update({"iat": issued_at})

    encoded_jwt = jwt.encode(
        claims=to_encode, key=env.ACCESS_TOKEN_SECRET_KEY, algorithm=ALGORITHM
    )

    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """
    Decode access token

    :param token: The user's token
    :return: The decoded token data
    """

    try:
        payload = jwt.decode(
            token=token, key=env.ACCESS_TOKEN_SECRET_KEY, algorithms=[ALGORITHM]
        )
        username: str = payload.get("sub")
        exp: int = payload.get("exp")
        if not username:
            raise http_exceptions.UnauthorizedHTTPException("Authentication failed")

        return {"username": username, "exp": exp}
    except JWTError:
        raise http_exceptions.UnauthorizedHTTPException("Authentication failed")


def auth_wrapper_access_token(token: str = Depends(oauth2_scheme_access)) -> str:
    """
    Authorization wrapper for access token
    Validate the access token and return the username

    :param token: The JWT access token
    :return: The username
    """

    token_data = decode_access_token(token=token)
    username = token_data.get("username")
    if username:
        return username

    raise http_exceptions.UnauthorizedHTTPException("Authentication failed")
