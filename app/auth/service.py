"""Authentication helper functions."""

from __future__ import annotations

import datetime as dt
from typing import Annotated, Any

import jwt
from fastapi import Depends

from app.auth.core import oauth2_scheme
from app.auth.schemas import TokenData
from app.settings import auth_settings


def verify_admin_username_password(username: str, password: str) -> bool:
    return bool(username == auth_settings.admin_username and password == auth_settings.admin_password)


def create_access_token(
    data: dict[str, Any],
    expires_delta: dt.timedelta = dt.timedelta(minutes=auth_settings.access_token_expire_minutes),
) -> str:
    """Create access token."""
    to_encode = data.copy()
    expire = dt.datetime.now(dt.UTC) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, auth_settings.secret_key, algorithm=auth_settings.algorithm)


def create_refresh_token(
    data: dict[str, Any],
    expires_delta: dt.timedelta = dt.timedelta(minutes=auth_settings.refresh_token_expire_minutes),
) -> str:
    """Create refresh token."""
    return create_access_token(data, expires_delta)


def verify_token(token: str) -> TokenData | None:
    """Verify a JWT token and return TokenData if valid."""
    try:
        payload = jwt.decode(token, auth_settings.secret_key, algorithms=[auth_settings.algorithm])
        username = payload.get("sub")
        if username is None:
            return None
        return TokenData(username=username)
    except jwt.InvalidTokenError:
        return None


def authenticate(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> bool:
    try:
        payload = jwt.decode(token, auth_settings.secret_key, algorithms=[auth_settings.algorithm])
        username = payload.get("sub")
        if username == auth_settings.admin_username:
            return True
    except jwt.InvalidTokenError:
        pass

    return True
