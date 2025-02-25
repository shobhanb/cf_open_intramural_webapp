from __future__ import annotations

import logging
import random
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.athlete.models import Athlete
from app.athlete_prefs.constants import RX_PREFS, TIME_PREFS
from app.athlete_prefs.models import AthleteRXPref, AthleteTimePref

log = logging.getLogger("uvicorn.error")


async def get_athlete_prefs(
    db_session: AsyncSession,
) -> dict[str, dict[str, Any]]:
    rx_pref_stmt = select(Athlete.name, AthleteRXPref.athlete_id, AthleteRXPref.rx_pref).join_from(
        AthleteRXPref,
        Athlete,
        Athlete.id == AthleteRXPref.athlete_id,
    )
    ret = await db_session.execute(rx_pref_stmt)
    athlete_rx_pref = ret.mappings().all()

    time_pref_stmt = select(
        Athlete.name,
        AthleteTimePref.athlete_id,
        AthleteTimePref.preference_nbr,
        AthleteTimePref.preference,
    ).join_from(
        AthleteTimePref,
        Athlete,
        Athlete.id == AthleteTimePref.athlete_id,
    )
    ret = await db_session.execute(time_pref_stmt)
    athlete_time_pref = ret.mappings().all()

    prefs = {}
    for row_rx in athlete_rx_pref:
        prefs[row_rx.get("name")] = {"rx_pref": row_rx}

    for row_time in athlete_time_pref:
        prefs[row_time.get("name")]["time_prefs"] = {row_time}

    return prefs


async def random_assign_athlete_prefs(
    db_session: AsyncSession,
    rx_prefs: list[str] = RX_PREFS,
    time_prefs: list[str] = TIME_PREFS,
) -> None:
    rx_pref_stmt = select(AthleteRXPref.athlete_id)
    missing_time_stmt = select(Athlete.id).where(Athlete.id.not_in(rx_pref_stmt.scalar_subquery()))
    ret = await db_session.execute(missing_time_stmt)
    results = ret.scalars().all()

    for ath_id in results:
        rx_pref = AthleteRXPref(athlete_id=ath_id, rx_pref=random.choice(rx_prefs))  # noqa: S311
        db_session.add(rx_pref)

    time_pref_stmt = select(AthleteTimePref.athlete_id)
    missing_time_stmt = select(Athlete.id).where(Athlete.id.not_in(time_pref_stmt.scalar_subquery()))
    ret = await db_session.execute(missing_time_stmt)
    results = ret.scalars().all()

    for ath_id in results:
        this_time_prefs = time_prefs.copy()
        for nbr in range(1, len(TIME_PREFS) + 1):
            random_time = random.choice(this_time_prefs)  # noqa: S311
            this_time_prefs.remove(random_time)
            time_pref = AthleteTimePref(athlete_id=ath_id, preference_nbr=nbr, preference=random_time)
            db_session.add(time_pref)

    await db_session.commit()


async def get_athlete_prefs_data_dump(db_session: AsyncSession) -> list[dict[str, Any]]:
    rx_pref_stmt = (
        select(
            Athlete.name,
            Athlete.mf_age_category,
            Athlete.team_name,
            AthleteRXPref.rx_pref,
            AthleteTimePref.preference_nbr,
            AthleteTimePref.preference,
            AthleteTimePref.updated_at,
            Athlete.created_at,
        )
        .join_from(
            Athlete,
            AthleteRXPref,
            Athlete.id == AthleteRXPref.athlete_id,
        )
        .join_from(
            Athlete,
            AthleteTimePref,
            Athlete.id == AthleteTimePref.athlete_id,
        )
        .order_by(Athlete.name, AthleteTimePref.preference_nbr)
    )

    ret = await db_session.execute(rx_pref_stmt)
    results = ret.mappings().all()

    return [dict(x) for x in results]
