"""Authentication helper functions."""

from __future__ import annotations

import datetime as dt
from typing import Any

import jwt
from fastapi import Request

from app.auth.schemas import TokenData
from app.settings import auth_settings


def verify_admin_username_password(username: str, password: str) -> bool:
    return bool(
        username.casefold() == auth_settings.admin_username.casefold() and password == auth_settings.admin_password,
    )


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


def authenticate_request(request: Request) -> str | None:
    access_token = request.cookies.get("access_token")
    if access_token:
        access_token_data = verify_token(access_token)
        if access_token_data:
            return access_token_data.username
    return None


def add_item_to_header(request: Request, key: str, value: str) -> Request:
    headers = dict(request.scope["headers"])
    headers[key.encode()] = value.encode()
    request.scope["headers"] = list(headers.items())
    return request
