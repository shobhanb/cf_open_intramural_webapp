import logging

from fastapi import APIRouter, Request, Response, status
from fastapi.responses import HTMLResponse

from app.athlete.service import get_athlete_teams
from app.auth.exceptions import unauthorised_exception
from app.auth.service import authenticate_request
from app.database.dependencies import db_dependency
from app.ui.template import templates

log = logging.getLogger("uvicorn.error")

ADMIN = True

athlete_router = APIRouter()


@athlete_router.get("/team_members", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def get_team_members(request: Request, db_session: db_dependency) -> Response:
    teams = await get_athlete_teams(db_session=db_session)
    return templates.TemplateResponse(
        request=request,
        name="pages/team_members.jinja2",
        context={
            "teams": teams,
        },
    )


@athlete_router.get("/assign_teams", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def get_assign_teams_page(request: Request, db_session: db_dependency) -> Response:
    user = authenticate_request(request)
    if not user:
        raise unauthorised_exception()

    teams = await get_athlete_teams(db_session=db_session)
    return templates.TemplateResponse(
        request=request,
        name="pages/assign_teams.jinja2",
        context={
            "teams": teams,
        },
    )
