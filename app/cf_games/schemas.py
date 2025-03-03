from __future__ import annotations

from typing import Self

from pydantic import Field, field_validator, model_validator

from app.schemas import CustomBaseModel


class CFDataCountModel(CustomBaseModel):
    year: int
    affiliate_id: int
    entrant_count: int
    score_count: int


class CFEntrantInputModel(CustomBaseModel):
    competitor_id: int = Field(alias="competitorId")
    name: str = Field(alias="competitorName")
    first_name: str = Field(alias="firstName")
    last_name: str = Field(alias="lastName")
    gender: str
    division_id: int = Field(alias="divisionId")
    affiliate_id: int = Field(alias="affiliateId")
    affiliate_name: str = Field(alias="affiliateName")
    age: str

    @field_validator("name", "first_name", "last_name", mode="before")
    @classmethod
    def to_title(cls, value: str) -> str:
        return value.title()


class CFScoreInputModel(CustomBaseModel):
    ordinal: int
    rank: int
    score: int
    valid: bool
    score_display: str = Field(alias="scoreDisplay")
    scaled: int
    breakdown: str | None
    time: int | None = None
    judge_name: str | None = Field(alias="judge", default="")
    judge_user_id: int | None = None
    affiliate: str | None = None

    @field_validator("judge_name", mode="before")
    @classmethod
    def to_title(cls, value: str) -> str:
        return value.title()

    @field_validator("valid", mode="before")
    @classmethod
    def make_valid_bool(cls, value: str) -> bool:
        return value == "1"

    @field_validator("time", "judge_user_id", mode="before")
    @classmethod
    def empty_to_none(cls, value: str) -> str | None:
        if value == "":
            return None
        return value

    @model_validator(mode="after")
    def apply_scale_adj(self) -> Self:
        if self.score == 0:
            self.scaled = 2
        return self
