import logging

from fastapi import APIRouter, Request, Response, status
from fastapi.responses import HTMLResponse

from app.auth.exceptions import not_found_exception
from app.cf_games.constants import EVENT_NAMES
from app.database.dependencies import db_dependency
from app.score.service import get_all_athlete_scores, get_db_team_scores, get_leaderboard_scores, get_total_scores
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
        },
    )
