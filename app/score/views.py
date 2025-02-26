import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Form, Request, Response, status
from fastapi.responses import HTMLResponse
from sqlalchemy import select

from app.athlete.service import get_team_names
from app.cf_games.constants import DEFAULT_SIDE_SCORE, EVENT_NAMES, TEAM_LOGOS
from app.database.dependencies import db_dependency
from app.exceptions import not_found_exception
from app.score.models import SideScore
from app.score.service import (
    get_all_athlete_scores,
    get_db_team_scores,
    get_leaderboard_scores,
    get_team_name_max_score,
    get_total_scores,
)
from app.ui.template import templates

log = logging.getLogger("uvicorn.error")

ADMIN = True

score_router = APIRouter()


@score_router.get("/team_scores/{ordinal}", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def get_team_scores_ordinal(
    ordinal: int,
    request: Request,
    db_session: db_dependency,
) -> Response:
    if ordinal not in EVENT_NAMES:
        raise not_found_exception()
    scores = await get_db_team_scores(db_session=db_session, ordinal=ordinal)
    overall_score = await get_total_scores(db_session=db_session)
    return templates.TemplateResponse(
        request=request,
        name="pages/team_scores.jinja2",
        context={
            "scores": scores,
            "overall_score": overall_score,
            "event_name": EVENT_NAMES.get(ordinal),
        },
    )


@score_router.get("/leaderboard/{ordinal}", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def get_leaderboard_ordinal(
    ordinal: int,
    request: Request,
    db_session: db_dependency,
) -> Response:
    if ordinal not in EVENT_NAMES:
        raise not_found_exception()
    leaderboard = await get_leaderboard_scores(db_session=db_session, ordinal=ordinal)
    return templates.TemplateResponse(
        request=request,
        name="pages/leaderboard.jinja2",
        context={
            "leaderboard": leaderboard,
            "event_name": EVENT_NAMES.get(ordinal),
        },
    )


@score_router.get("/athlete_scores/{ordinal}", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def get_athlete_scores(
    ordinal: int,
    request: Request,
    db_session: db_dependency,
) -> Response:
    if ordinal not in EVENT_NAMES:
        raise not_found_exception()
    scores = await get_all_athlete_scores(db_session=db_session, ordinal=ordinal)
    return templates.TemplateResponse(
        request=request,
        name="pages/athlete_scores.jinja2",
        context={
            "scores": scores,
            "event_name": EVENT_NAMES.get(ordinal),
        },
    )


@score_router.get("/side_scores", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def get_side_scores_page(
    request: Request,
    db_session: db_dependency,
) -> Response:
    teams = await get_team_names(db_session=db_session)
    side_score_stmt = select(SideScore).order_by(SideScore.event_name, SideScore.score_type)
    result = await db_session.execute(side_score_stmt)
    side_scores = result.scalars().all()
    return templates.TemplateResponse(
        request=request,
        name="pages/side_scores.jinja2",
        context={
            "side_scores": side_scores,
            "teams": teams,
            "default_score": DEFAULT_SIDE_SCORE,
        },
    )


@score_router.delete("/side_scores/{id_}", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def delete_side_score_id(
    request: Request,
    db_session: db_dependency,
    id_: UUID,
) -> Response:
    side_score = await SideScore.get(async_session=db_session, id_=id_)
    if side_score:
        await side_score.delete(async_session=db_session)

    teams = await get_team_names(db_session=db_session)
    side_score_stmt = select(SideScore).order_by(SideScore.event_name, SideScore.score_type)
    result = await db_session.execute(side_score_stmt)
    side_scores = result.scalars().all()

    return templates.TemplateResponse(
        request=request,
        name="partials/side_scores_table.jinja2",
        context={
            "side_scores": side_scores,
            "teams": teams,
            "default_score": DEFAULT_SIDE_SCORE,
        },
    )


@score_router.post("/side_scores", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def post_side_score_new(  # noqa: PLR0913
    request: Request,
    db_session: db_dependency,
    event_name: Annotated[str, Form()],
    score_type: Annotated[str, Form()],
    team_name: Annotated[str, Form()],
    score: Annotated[int, Form()],
) -> Response:
    teams = await get_team_names(db_session=db_session)

    if event_name in EVENT_NAMES.values() and score_type in ["side_challenge", "spirit"] and team_name in teams:
        side_score = SideScore(event_name=event_name, score_type=score_type, team_name=team_name, score=score)
        db_session.add(side_score)
        await db_session.commit()

    side_score_stmt = select(SideScore).order_by(SideScore.event_name, SideScore.score_type)
    result = await db_session.execute(side_score_stmt)
    side_scores = result.scalars().all()

    return templates.TemplateResponse(
        request=request,
        name="partials/side_scores_table.jinja2",
        context={
            "side_scores": side_scores,
            "teams": teams,
            "default_score": DEFAULT_SIDE_SCORE,
        },
    )


@score_router.get("/leading_teams_imgs", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def get_leading_teams_imgs(
    request: Request,
    db_sesion: db_dependency,
) -> Response:
    leading_teams = await get_team_name_max_score(db_session=db_sesion)
    leading_teams_logos = [TEAM_LOGOS.get(x) for x in leading_teams]

    return templates.TemplateResponse(
        request=request,
        name="partials/leading_teams.jinja2",
        context={
            "leading_logos": leading_teams_logos,
        },
    )
