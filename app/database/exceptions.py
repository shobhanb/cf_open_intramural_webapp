from fastapi import status
from fastapi.exceptions import HTTPException


def not_found_error(msg: str = "Resource not found") -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)


def conflict_error(msg: str = "Resource conflict") -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=msg)


class DBSessionNotInitializedError(Exception):
    pass
