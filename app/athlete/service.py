from uuid import UUID

from sqlalchemy import select

from app.athlete.models import Athlete
from app.cf_games.constants import AFFILIATE_ID, YEAR
from app.database.dependencies import db_dependency


async def get_year_affiliate_athletes(
    db_session: db_dependency,
    year: int = int(YEAR),
    affiliate_id: int = int(AFFILIATE_ID),
) -> list[UUID]:
    stmt = select(Athlete.id).where((Athlete.year == year) & (Athlete.affiliate_id == affiliate_id))
    result = await db_session.execute(stmt)
    return list(result.scalars())


async def get_athlete_teams(
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
