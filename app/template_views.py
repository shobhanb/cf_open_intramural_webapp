import logging

from fastapi import APIRouter, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.cf_games.constants import EVENT_NAMES, RENDER_CONTEXT
from app.cf_games.service import process_cf_data
from app.database.dependencies import db_dependency
from app.score.service import get_db_team_scores, get_leaderboard_scores, get_total_scores

log = logging.getLogger("uvicorn.error")

template_router = APIRouter()

templates = Jinja2Templates(directory="templates")


@template_router.get("/", response_class=RedirectResponse, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
@template_router.get("/team_scores", response_class=RedirectResponse, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
async def team_scores_redirect() -> RedirectResponse:
    return RedirectResponse(url="/team_scores/1")


@template_router.get("/team_scores/{ordinal}", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def get_team_scores_ordinal(ordinal: int, request: Request, db_session: db_dependency) -> HTMLResponse:
    scores = await get_db_team_scores(db_session=db_session, ordinal=ordinal)
    overall_score = await get_total_scores(db_session=db_session)
    return templates.TemplateResponse(
        request=request,
        name="pages/team_scores.jinja2",
        context={
            "scores": scores,
            "overall_score": overall_score,
            "event_name": EVENT_NAMES[ordinal],
            "info": RENDER_CONTEXT,
            "admin": False,
        },
    )


@template_router.get("/leaderboard/{ordinal}", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def get_leaderboard_ordinal(ordinal: int, request: Request, db_session: db_dependency) -> HTMLResponse:
    leaderboard = await get_leaderboard_scores(db_session=db_session, ordinal=ordinal)
    return templates.TemplateResponse(
        request=request,
        name="pages/leaderboard.jinja2",
        context={"leaderboard": leaderboard, "event_name": EVENT_NAMES[ordinal], "info": RENDER_CONTEXT, "admin": True},
    )


@template_router.get("/refresh", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def refresh_cf_games_data(db_session: db_dependency) -> RedirectResponse:
    await process_cf_data(db_session=db_session)
    return await team_scores_redirect()
