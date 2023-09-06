import os
from datetime import datetime, timedelta

from fastapi import Depends
from jose import jwt, JWTError

from app import http_exceptions, constants
from app.oauth2_password_bearer_with_cookie import OAuth2PasswordBearerWithCookie

ACCESS_TOKEN_SECRET_KEY = os.getenv("ACCESS_TOKEN_SECRET_KEY")
ALGORITHM = "HS256"

oauth2_scheme_access = OAuth2PasswordBearerWithCookie(tokenUrl="/api/v1/auth/login")


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
        claims=to_encode, key=ACCESS_TOKEN_SECRET_KEY, algorithm=ALGORITHM
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
            token=token, key=ACCESS_TOKEN_SECRET_KEY, algorithms=[ALGORITHM]
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
