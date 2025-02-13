from __future__ import annotations

from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class AthleteRXPref(Base):
    athlete_id: Mapped[UUID] = mapped_column(ForeignKey("athlete.id"), unique=True)
    rx_pref: Mapped[str] = mapped_column(String)


class AthleteTimePref(Base):
    __table_args__ = (UniqueConstraint("athlete_id", "preference_nbr"), UniqueConstraint("athlete_id", "preference"))

    athlete_id: Mapped[UUID] = mapped_column(ForeignKey("athlete.id"))
    preference_nbr: Mapped[int] = mapped_column(Integer, default=1)
    preference: Mapped[str] = mapped_column(String, default="")
