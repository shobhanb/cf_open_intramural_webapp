from __future__ import annotations

import asyncio
import csv
import logging
from pathlib import Path

from httpx import AsyncClient, HTTPError
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.athlete.models import Athlete
from app.cf_games.constants import (
    AFFILIATE_ID,
    ATTENDANCE_FILEPATH,
    ATTENDANCE_SCORE,
    CF_DIVISION_MAP,
    CF_LEADERBOARD_URL,
    JUDGE_SCORE,
    PARTICIPATION_SCORE,
    SIDE_CHALLENGE_SCORE,
    SPIRIT_FILEPATH,
    SPIRIT_SCORE,
    TOP3_SCORE,
    YEAR,
)
from app.cf_games.schemas import CFDataCountModel, CFEntrantInputModel, CFScoreInputModel
from app.score.models import Score, SideScore

log = logging.getLogger("uvicorn.error")


async def cf_data_api(  # noqa: PLR0913
    httpx_client: AsyncClient,
    api_url: str,
    affiliate_code: int,
    division: int,
    entrant_list: list[dict],
    scores_list: list[dict],
) -> None:
    total_pages = 1
    page = 1
    while True:
        params = {"affiliate": affiliate_code, "page": page, "per_page": 100, "view": 0, "division": division}
        response = await httpx_client.get(url=api_url, params=params)

        json_response = response.json()
        leaderboard_list = json_response.get("leaderboardRows", [])
        entrants = [x.get("entrant") for x in leaderboard_list]
        entrant_list.extend(entrants)
        scores = [x.get("scores") for x in leaderboard_list]
        scores_list.extend(scores)

        # Handle pagination
        total_pages = json_response.get("pagination", {}).get("totalPages", 1)
        if total_pages <= page:
            break

        page += 1


async def get_cf_data(affiliate_code: int, year: int) -> tuple[int, list[dict], list[dict]]:
    """Get CF leaderboard data."""
    log.info("Getting CF Leaderboard data for year %s affiliate code %s", year, affiliate_code)
    entrant_list = []
    scores_list = []

    api_url = CF_LEADERBOARD_URL.replace("YYYY", str(year))

    try:
        async with AsyncClient(timeout=10.0) as aclient:
            await asyncio.gather(
                *[
                    cf_data_api(
                        httpx_client=aclient,
                        api_url=api_url,
                        affiliate_code=affiliate_code,
                        division=int(x),
                        entrant_list=entrant_list,
                        scores_list=scores_list,
                    )
                    for x in CF_DIVISION_MAP
                ],
            )

    except HTTPError:
        log.exception("HTTP Exception while getting CF data")

    log.info("Downloaded %s entrants, %s scores", len(entrant_list), len(scores_list))
    return year, entrant_list, scores_list


async def process_cf_data(
    db_session: AsyncSession,
    affiliate_id: int = AFFILIATE_ID,
    year: int = YEAR,
) -> CFDataCountModel:
    year, entrant_list, scores_list = await get_cf_data(affiliate_id, year)

    await Score.delete_all(async_session=db_session)

    for entrant, scores in zip(entrant_list, scores_list, strict=True):
        entrant_model = CFEntrantInputModel.model_validate(entrant)
        athlete = await Athlete.find(async_session=db_session, competitor_id=entrant_model.competitor_id)
        if athlete is None:
            athlete = Athlete(**entrant_model.model_dump(), year=year)
            db_session.add(athlete)

        if scores:
            for score in scores:
                score_model = CFScoreInputModel.model_validate(score)
                event_score = await Score.find(
                    async_session=db_session,
                    athlete_id=athlete.id,
                    ordinal=score_model.ordinal,
                )
                if event_score:
                    for var, value in vars(score_model).items():
                        setattr(event_score, var, value) if value else None
                else:
                    event_score = Score(
                        **score_model.model_dump(),
                        athlete=athlete,
                    )
                if event_score.score > 0:
                    event_score.participation_score = PARTICIPATION_SCORE
                db_session.add(event_score)

    await db_session.commit()

    await apply_top3_score(db_session=db_session)
    # await apply_attendance_scores(db_session=db_session)
    await apply_judge_score(db_session=db_session)
    await apply_side_scores(db_session=db_session)
    await apply_total_score(db_session=db_session)

    return CFDataCountModel(
        year=year,
        affiliate_id=affiliate_id,
        entrant_count=len(entrant_list),
        score_count=len(scores_list),
    )


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
    with Path(ATTENDANCE_FILEPATH).open() as file:  # noqa: ASYNC230
        reader = csv.reader(file)
        for row in reader:
            if row[0] in attendance:
                attendance[row[0]].append(row[1].title())
            else:
                attendance[row[0]] = [row[1].title()]

    for k, v in attendance.items():
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
    await db_session.execute(select_stmt)


async def apply_judge_score(
    db_session: AsyncSession,
) -> None:
    select_judge_stmt = select(Score.judge_name, Score.ordinal).distinct()
    result = await db_session.execute(select_judge_stmt)
    judges = result.mappings().all()
    for row in judges:
        select_score_stmt = (
            select(Score.id)
            .join_from(Score, Athlete, Score.athlete_id == Athlete.id)
            .where((Athlete.name == row.get("judge_name")) & (Score.ordinal == row.get("ordinal")))
        )
        update_stmt = (
            update(Score).where(Score.id.in_(select_score_stmt.scalar_subquery())).values(judge_score=JUDGE_SCORE)
        )
        await db_session.execute(update_stmt)

    await db_session.commit()


async def apply_side_scores(
    db_session: AsyncSession,
    side_challenge_score: int = SIDE_CHALLENGE_SCORE,
    spirit_score: int = SPIRIT_SCORE,
) -> None:
    side_scores = await SideScore.all(async_session=db_session)

    for side_score in side_scores:
        select_stmt = (
            (
                select(Score)
                .join_from(Score, Athlete, Score.athlete_id == Athlete.id)
                .where((Score.event_name == side_score.event_name) & (Athlete.team_name == side_score.team_name))
            )
            .order_by(Athlete.team_leader.desc())
            .limit(1)
        )
        result = await db_session.execute(select_stmt)
        score = result.scalar_one()

        if side_score.score_type == "side_challenge":
            score.side_challenge_score = side_challenge_score
            db_session.add(score)
            await db_session.commit()
        elif side_score.score_type == "spirit":
            score.spirit_score = spirit_score
            db_session.add(score)
            await db_session.commit()


async def apply_spirit_score(
    db_session: AsyncSession,
) -> None:
    with Path(SPIRIT_FILEPATH).open() as file:  # noqa: ASYNC230
        reader = csv.reader(file)
        for row in reader:
            select_stmt = (
                (
                    select(Score.id)
                    .join_from(Score, Athlete, Score.athlete_id == Athlete.id)
                    .where((Score.event_name == row[0]) & (Athlete.team_name == row[1]))
                )
                .order_by(Athlete.team_leader.desc())
                .limit(1)
            )
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
