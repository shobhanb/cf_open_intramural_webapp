from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.athlete.models import Athlete
from app.cf_games.constants import IGNORE_TEAMS
from app.score.models import Score

log = logging.getLogger("uvicorn.error")


async def get_db_team_scores(
    db_session: AsyncSession,
    ordinal: int,
) -> dict[str, dict[str, Any]]:
    team_score_stmt = (
        select(
            Athlete.team_name,
            func.count().label("count"),
            func.sum(Score.participation_score).label("participation"),
            func.sum(Score.top3_score).label("top3_score"),
            func.sum(Score.attendance_score).label("attendance_score"),
            func.sum(Score.judge_score).label("judge_score"),
            func.sum(Score.appreciation_score).label("appreciation_score"),
            func.sum(Score.side_challenge_score).label("side_challenge_score"),
            func.sum(Score.spirit_score).label("spirit_score"),
            func.sum(Score.total_score).label("total_score"),
        )
        .join_from(Score, Athlete, Score.athlete_id == Athlete.id)
        .where((Score.ordinal == ordinal) & (Athlete.team_name.not_in(IGNORE_TEAMS)))
        .group_by(Athlete.team_name)
        .order_by(Athlete.team_name)
    )
    ret = await db_session.execute(team_score_stmt)

    result = ret.mappings().all()
    team_scores = {}
    for row in result:
        name = row.get("team_name", "")
        team_scores[name] = row

    return team_scores


async def get_total_scores(db_session: AsyncSession) -> dict[str, dict[str, Any]]:
    total_score_stmt = (
        select(
            Athlete.team_name,
            func.sum(Score.total_score).label("overall_score"),
        )
        .join_from(Score, Athlete, Score.athlete_id == Athlete.id)
        .where(Athlete.team_name.not_in(IGNORE_TEAMS))
        .group_by(Athlete.team_name)
        .order_by(Athlete.team_name)
    )

    ret = await db_session.execute(total_score_stmt)

    result = ret.mappings().all()
    overall_scores = {}
    for row in result:
        name = row.get("team_name", "")
        overall_scores[name] = row

    return overall_scores


async def get_leaderboard_scores(
    db_session: AsyncSession,
    ordinal: int,
) -> dict[str, dict[str, Any]]:
    stmt = (
        select(
            Athlete.name,
            Athlete.gender,
            Athlete.mf_age_category,
            Athlete.team_name,
            Score.affiliate_scaled,
            Score.affiliate_rank,
            Score.score_display,
        )
        .join_from(Score, Athlete, Score.athlete_id == Athlete.id)
        .where((Score.ordinal == ordinal) & (Score.affiliate_rank <= 3))  # noqa: PLR2004
        .order_by(
            Athlete.gender,
            Athlete.mf_age_category.asc(),
            Score.affiliate_scaled,
            Score.scaled,
            Score.score.desc(),
            Score.rank.desc(),
            Athlete.name,
        )
    )
    ret = await db_session.execute(stmt)
    result = ret.mappings().all()
    leaderboard = {}
    for row in result:
        category = row.get("mf_age_category", "") + "-" + row.get("gender", "")
        if category in leaderboard:
            leaderboard[category].append(row)
        else:
            leaderboard[category] = [row]
    return leaderboard


async def get_all_athlete_scores(
    db_session: AsyncSession,
    ordinal: int,
) -> dict[str, dict[str, Any]]:
    stmt = (
        select(
            Athlete.name,
            Athlete.gender,
            Athlete.mf_age_category,
            Athlete.team_name,
            Athlete.team_leader,
            Score.affiliate_scaled,
            Score.affiliate_rank,
            Score.score_display,
            Score.reps,
            Score.time_ms,
            Score.tiebreak_ms,
            Score.judge_name,
            Score.participation_score,
            Score.top3_score,
            Score.attendance_score,
            Score.judge_score,
            Score.appreciation_score,
            Score.side_challenge_score,
            Score.spirit_score,
            Score.total_score,
            Score.valid,
        )
        .join_from(Score, Athlete, Score.athlete_id == Athlete.id)
        .where(Score.ordinal == ordinal)
        .order_by(
            Athlete.gender,
            Athlete.mf_age_category.asc(),
            Score.affiliate_scaled,
            Score.scaled,
            Score.score.desc(),
            Score.rank.desc(),
            Athlete.name,
        )
    )
    ret = await db_session.execute(stmt)
    result = ret.mappings().all()
    leaderboard = {}
    for row in result:
        category = row.get("mf_age_category", "") + "-" + row.get("gender", "")
        if category in leaderboard:
            leaderboard[category].append(row)
        else:
            leaderboard[category] = [row]
    return leaderboard


async def get_team_name_max_score(db_session: AsyncSession) -> list[str]:
    total_score_stmt = (
        select(
            Athlete.team_name,
            func.sum(Score.total_score).label("overall_score"),
        )
        .join_from(Score, Athlete, Score.athlete_id == Athlete.id)
        .group_by(Athlete.team_name)
        .order_by(Athlete.team_name)
    )

    ret = await db_session.execute(total_score_stmt)
    result = ret.mappings().all()

    teams = [row["team_name"] for row in result]
    scores = [row["overall_score"] for row in result]

    if len(teams) == 0:
        return []

    max_score = max(scores)
    return [team for team, score in zip(teams, scores, strict=True) if score == max_score]
