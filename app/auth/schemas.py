from __future__ import annotations

from app.schemas import CustomBaseModel


class Token(CustomBaseModel):
    access_token: str
    token_type: str


class TokenData(CustomBaseModel):
    username: str | None = None
