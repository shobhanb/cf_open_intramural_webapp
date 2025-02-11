from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Integer, String
from sqlalchemy.engine.default import DefaultExecutionContext
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.cf_games.constants import CF_DIVISION_MAP, MF_MASTERS_AGE_CUTOFF, MF_OPEN_AGE_CUTOFF
from app.database.base import Base

if TYPE_CHECKING:
    from app.score.models import Score


def apply_mf_age_category(context: DefaultExecutionContext) -> str:
    age = context.get_current_parameters()["age"]
    if int(age) >= int(MF_MASTERS_AGE_CUTOFF):
        return "3. Masters 55+"
    if int(age) >= int(MF_OPEN_AGE_CUTOFF):
        return "2. Masters"
    return "1. Open"


def apply_division_name(context: DefaultExecutionContext) -> str:
    division_id = context.get_current_parameters()["division_id"]
    return CF_DIVISION_MAP[str(division_id)]


class Athlete(Base):
    # PK / FK
    competitor_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    year: Mapped[int] = mapped_column(Integer, primary_key=True)

    # CF Games data
    affiliate_id: Mapped[int] = mapped_column(Integer)
    affiliate_name: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String)
    first_name: Mapped[str] = mapped_column(String)
    last_name: Mapped[str] = mapped_column(String)
    gender: Mapped[str] = mapped_column(String)
    division_id: Mapped[int] = mapped_column(Integer)
    age: Mapped[int] = mapped_column(Integer)

    # Affiliate columns
    mf_age_category: Mapped[str] = mapped_column(String, default=apply_mf_age_category)
    team_name: Mapped[str] = mapped_column(String, default="zz")
    team_leader: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    scores: Mapped[list[Score]] = relationship(back_populates="athlete")
