from __future__ import annotations

import asyncio
import logging

import aiofiles
import httpx
from aiocsv import AsyncReader
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.athlete.models import Athlete
from app.cf_games.constants import (
    AFFILIATE_ID,
    ATTENDANCE_FILEPATH,
    ATTENDANCE_SCORE,
    CF_API_REQUEST_THROTTLE_SECONDS,
    CF_LEADERBOARD_URL,
    JUDGE_SCORE,
    PARTICIPATION_SCORE,
    SIDE_CHALLENGE_FILEPATH,
    SPIRIT_FILEPATH,
    TEAM_ASSIGNMENTS_FILEPATH,
    TOP3_SCORE,
    YEAR,
)
from app.cf_games.schemas import CFDataCountModel, CFEntrantInputModel, CFScoreInputModel
from app.score.models import Score

log = logging.getLogger("uvicorn.error")


async def get_cf_data(affiliate_code: int, year: int) -> tuple[int, list[dict], list[dict]]:
    """Get CF leaderboard data."""
    log.info("Getting CF Leaderboard data for year %s affiliate code %s", year, affiliate_code)
    entrant_list = []
    scores_list = []

    api_url = CF_LEADERBOARD_URL.replace("YYYY", str(year))
    aclient = httpx.AsyncClient()

    # Only pull division 1 (Men) & 2 (Women) because it includes all details.
    # Pulling other divisions would be double counting.
    for id_ in range(1, 50):
        total_pages = 1
        page = 1
        while True:
            params = {"affiliate": affiliate_code, "page": page, "per_page": 100, "view": 0, "division": id_}
            response = await aclient.get(url=api_url, params=params)

            json_response = response.json()
            leaderboard_list = json_response.get("leaderboardRows", [])
            entrants = [
                x.get("entrant") for x in leaderboard_list if int(x.get("entrant", {}).get("divisionId")) == id_
            ]
            entrant_list.extend(entrants)
            scores = [x.get("scores") for x in leaderboard_list if int(x.get("entrant", {}).get("divisionId")) == id_]
            scores_list.extend(scores)

            # Handle pagination
            total_pages = json_response.get("pagination", {}).get("totalPages", 1)
            if total_pages <= page:
                break

            page += 1
            # Throttle requests
            await asyncio.sleep(CF_API_REQUEST_THROTTLE_SECONDS)

    await aclient.aclose()

    log.info("Downloaded %s entrants, %s scores", len(entrant_list), len(scores_list))
    return year, entrant_list, scores_list


async def process_cf_data(
    db_session: AsyncSession,
    affiliate_id: int = AFFILIATE_ID,
    year: int = YEAR,
) -> CFDataCountModel:
    year, entrant_list, scores_list = await get_cf_data(affiliate_id, year)

    delete_score_stmt = delete(Score)
    delete_athlete_stmt = delete(Athlete)

    await db_session.execute(delete_score_stmt)
    await db_session.execute(delete_athlete_stmt)
    await db_session.commit()

    for entrant, scores in zip(entrant_list, scores_list, strict=True):
        entrant_model = CFEntrantInputModel.model_validate(entrant)
        athlete = Athlete(**entrant_model.model_dump(), year=year)
        db_session.add(athlete)

        if scores:
            for score in scores:
                score_model = CFScoreInputModel.model_validate(score)
                event_score = Score(
                    **score_model.model_dump(),
                    athlete=athlete,
                )
                if event_score.score > 0:
                    event_score.participation_score = PARTICIPATION_SCORE
                db_session.add(event_score)

    await db_session.commit()

    await apply_team_assignments(db_session=db_session)
    await apply_top3_score(db_session=db_session)
    await apply_attendance_scores(db_session=db_session)
    await apply_judge_score(db_session=db_session)
    await apply_side_challenge_score(db_session=db_session)
    await apply_spirit_score(db_session=db_session)
    await apply_total_score(db_session=db_session)

    return CFDataCountModel(
        year=year,
        affiliate_id=affiliate_id,
        entrant_count=len(entrant_list),
        score_count=len(scores_list),
    )


async def apply_team_assignments(
    db_session: AsyncSession,
) -> None:
    async with aiofiles.open(TEAM_ASSIGNMENTS_FILEPATH) as file:
        async for row in AsyncReader(file):
            update_stmt = update(Athlete).where(Athlete.name == row[0].title()).values(team_name=row[1])
            await db_session.execute(update_stmt)

    await db_session.commit()

    select_stmt = select(Athlete.name).where(Athlete.team_name == "Unassigned")
    results = await db_session.execute(select_stmt)
    log.info(results.scalars().all())


async def apply_ranks(
    db_session: AsyncSession,
) -> None:
    select_stmt = select(
        Score.id,
        func.rank()
        .over(
            partition_by=[Score.ordinal, Athlete.gender, Athlete.mf_age_category, Score.affiliate_scaled],
            order_by=[Score.scaled.asc(), Score.score.desc()],
        )
        .label("affiliate_rank"),
    ).join_from(Score, Athlete, Score.athlete_id == Athlete.id)
    ranks = await db_session.execute(select_stmt)
    values = ranks.mappings().all()
    await db_session.execute(update(Score), [dict(x) for x in values])
    await db_session.commit()


async def apply_top3_score(
    db_session: AsyncSession,
) -> None:
    await apply_ranks(db_session=db_session)
    stmt = update(Score).where(Score.affiliate_rank <= 3).values(top3_score=TOP3_SCORE)  # noqa: PLR2004
    await db_session.execute(stmt)
    await db_session.commit()


async def apply_attendance_scores(
    db_session: AsyncSession,
) -> None:
    attendance = {}
    async with aiofiles.open(ATTENDANCE_FILEPATH) as file:
        async for row in AsyncReader(file):
            if row[0] in attendance:
                attendance[row[0]].append(row[1].title())
            else:
                attendance[row[0]] = [row[1].title()]

    for k, v in attendance.items():
        log.info("Attendance event %s count %s", k, len(v))
        select_stmt = (
            select(Score.id)
            .join_from(Score, Athlete, Score.athlete_id == Athlete.id)
            .where((Score.event_name == k) & (Athlete.name.in_(v)))
        )
        update_stmt = (
            update(Score).where(Score.id.in_(select_stmt.scalar_subquery())).values(attendance_score=ATTENDANCE_SCORE)
        )
        await db_session.execute(update_stmt)

    await db_session.commit()

    select_stmt = select(Score.event_name, func.count()).where(Score.attendance_score > 0)
    results = await db_session.execute(select_stmt)
    log.info(results.scalars().all())


async def apply_judge_score(
    db_session: AsyncSession,
) -> None:
    select_judge_stmt = select(Score.judge_name, Score.ordinal).distinct()
    result = await db_session.execute(select_judge_stmt)
    judges = result.mappings().all()
    for row in judges:
        select_score_stmt = (
            select(Score.id)
            .join_from(Score, Athlete, Score.athlete_id == Score.id)
            .where((Athlete.name == row.get("judge_name")) & (Score.ordinal == row.get("ordinal")))
        )
        update_stmt = (
            update(Score).where(Score.id.in_(select_score_stmt.scalar_subquery())).values(judge_score=JUDGE_SCORE)
        )
        await db_session.execute(update_stmt)

    await db_session.commit()


async def apply_side_challenge_score(
    db_session: AsyncSession,
) -> None:
    async with aiofiles.open(SIDE_CHALLENGE_FILEPATH) as file:
        async for row in AsyncReader(file):
            select_stmt = (
                select(Score.id)
                .join_from(Score, Athlete, Score.athlete_id == Athlete.id)
                .where((Score.event_name == row[0]) & (Athlete.team_name == row[1]))
            ).limit(1)
            update_stmt = (
                update(Score).where(Score.id.in_(select_stmt.scalar_subquery())).values(side_challenge_score=row[2])
            )
            await db_session.execute(update_stmt)

    await db_session.commit()


async def apply_spirit_score(
    db_session: AsyncSession,
) -> None:
    async with aiofiles.open(SPIRIT_FILEPATH) as file:
        async for row in AsyncReader(file):
            select_stmt = (
                select(Score.id)
                .join_from(Score, Athlete, Score.athlete_id == Athlete.id)
                .where((Score.event_name == row[0]) & (Athlete.team_name == row[1]))
            ).limit(1)
            update_stmt = update(Score).where(Score.id.in_(select_stmt.scalar_subquery())).values(spirit_score=row[2])
            await db_session.execute(update_stmt)

    await db_session.commit()


async def apply_total_score(
    db_session: AsyncSession,
) -> None:
    update_stmt = update(Score).values(
        total_score=Score.participation_score
        + Score.top3_score
        + Score.judge_score
        + Score.attendance_score
        + Score.side_challenge_score
        + Score.spirit_score,
    )
    await db_session.execute(update_stmt)
    await db_session.commit()
