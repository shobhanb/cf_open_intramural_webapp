from __future__ import annotations

from fastapi import HTTPException, status


def unauthorised_exception(detail: str | None = None) -> HTTPException:
    if not detail:
        detail = "Incorrect username or password"
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
    )


def not_found_exception(detail: str | None = None) -> HTTPException:
    if not detail:
        detail = "Resource not found"
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=detail,
    )
