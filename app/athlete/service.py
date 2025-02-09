from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select, update

from app.athlete.models import Athlete
from app.cf_games.constants import AFFILIATE_ID, TEAM_LEADER_MAP, YEAR
from app.database.dependencies import db_dependency


async def get_year_affiliate_athletes(
    db_session: db_dependency,
    year: int = int(YEAR),
    affiliate_id: int = int(AFFILIATE_ID),
) -> list[UUID]:
    stmt = select(Athlete.id).where((Athlete.year == year) & (Athlete.affiliate_id == affiliate_id))
    result = await db_session.execute(stmt)
    return list(result.scalars())


async def get_athlete_teams_list(
    db_session: db_dependency,
) -> list[dict[str, Any]]:
    stmt = select(Athlete.name, Athlete.competitor_id, Athlete.team_name, Athlete.team_leader).order_by(
        Athlete.team_name,
        Athlete.team_leader.desc(),
        Athlete.name,
    )
    ret = await db_session.execute(stmt)
    return [dict(x) for x in ret.mappings().all()]


async def get_athlete_teams_dict(
    db_session: db_dependency,
) -> dict[str, list[str]]:
    stmt = select(Athlete.name, Athlete.team_name, Athlete.team_leader).order_by(
        Athlete.team_name,
        Athlete.team_leader.desc(),
        Athlete.name,
    )
    ret = await db_session.execute(stmt)
    teams = {}
    result = ret.mappings().all()
    for row in result:
        team_name = row.get("team_name")
        if team_name in teams:
            teams[team_name].append(row)
        else:
            teams[team_name] = [row]

    return teams


async def assign_athlete_to_team(
    db_session: db_dependency,
    competitor_id: int,
    team_name: str,
) -> None:
    athlete = await Athlete.find(async_session=db_session, competitor_id=competitor_id)
    if athlete:
        athlete.team_name = team_name
        db_session.add(athlete)
        await db_session.commit()


async def assign_athlete_team_role(
    db_session: db_dependency,
    competitor_id: int,
    tl_c: str,
) -> None:
    athlete = await Athlete.find(async_session=db_session, competitor_id=competitor_id)
    if athlete:
        athlete.team_leader = TEAM_LEADER_MAP.get(tl_c, 0)
        db_session.add(athlete)
        await db_session.commit()


async def get_team_names(
    db_session: db_dependency,
) -> list[str]:
    stmt = select(Athlete.team_name).distinct()
    ret = await db_session.execute(stmt)
    result = ret.scalars()
    return list(result)


async def rename_team(
    db_session: db_dependency,
    team_name_current: str,
    team_name_new: str,
) -> None:
    stmt = update(Athlete).where(Athlete.team_name == team_name_current).values(team_name=team_name_new)
    await db_session.execute(stmt)
    await db_session.commit()
