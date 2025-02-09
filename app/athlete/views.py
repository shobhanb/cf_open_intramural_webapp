import logging
from typing import Annotated

from fastapi import APIRouter, Form, Request, Response, status
from fastapi.responses import HTMLResponse

from app.athlete.service import get_athlete_teams_dict, get_athlete_teams_list
from app.auth.exceptions import unauthorised_exception
from app.auth.service import authenticate_request
from app.cf_games.constants import TEAM_LEADER_REVERSE_MAP
from app.database.dependencies import db_dependency
from app.ui.template import templates

log = logging.getLogger("uvicorn.error")

ADMIN = True

athlete_router = APIRouter()


@athlete_router.get("/team_members", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def get_team_members(request: Request, db_session: db_dependency) -> Response:
    teams = await get_athlete_teams_dict(db_session=db_session)
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

    teams = await get_athlete_teams_dict(db_session=db_session)
    return templates.TemplateResponse(
        request=request,
        name="pages/assign_teams.jinja2",
        context={
            "teams": teams,
        },
    )


@athlete_router.post("/athlete_teams", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def get_athlete_teams_partial(
    request: Request,
    db_session: db_dependency,
    name: Annotated[str, Form()],
) -> Response:
    user = authenticate_request(request)
    if not user:
        raise unauthorised_exception()

    athlete_teams = await get_athlete_teams_list(db_session=db_session)
    filtered_teams = [x for x in athlete_teams if name.casefold() in x.get("name", "").casefold()]
    for x in filtered_teams:
        x["tl_c"] = TEAM_LEADER_REVERSE_MAP.get(x.get("team_leader", 0), "")
    return templates.TemplateResponse(
        request=request,
        name="partials/athlete_teams_tbody.jinja2",
        context={
            "athlete_teams": filtered_teams,
        },
    )
