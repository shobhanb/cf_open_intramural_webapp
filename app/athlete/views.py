from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Form, Request, Response, status
from fastapi.responses import HTMLResponse

from app.athlete.service import (
    assign_athlete_team_role,
    assign_athlete_to_team,
    get_athlete_teams_dict,
    get_athlete_teams_list,
    get_team_names,
    rename_team,
)
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


@athlete_router.get("/rename_teams", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def get_rename_teams_page(request: Request, db_session: db_dependency) -> Response:
    user = authenticate_request(request)
    if not user:
        raise unauthorised_exception()

    teams = await get_team_names(db_session=db_session)
    return templates.TemplateResponse(
        request=request,
        name="pages/rename_teams.jinja2",
        context={
            "teams": teams,
        },
    )


@athlete_router.get("/auto_team_assign", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def get_auto_team_assign_page(request: Request, db_session: db_dependency) -> Response:
    user = authenticate_request(request)
    if not user:
        raise unauthorised_exception()

    teams = await get_athlete_teams_dict(db_session=db_session)
    return templates.TemplateResponse(
        request=request,
        name="pages/auto_team_assign.jinja2",
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


@athlete_router.put("/assign_athlete_team/{competitor_id}", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def put_assign_athlete_teams(
    request: Request,
    competitor_id: int,
    team_name: Annotated[str, Form()],
    db_session: db_dependency,
) -> Response:
    user = authenticate_request(request)
    if not user:
        raise unauthorised_exception()

    await assign_athlete_to_team(db_session=db_session, competitor_id=competitor_id, team_name=team_name)

    return HTMLResponse(content=f"<td>{team_name}</td>")


@athlete_router.put(
    "/assign_athlete_team_leader/{competitor_id}",
    response_class=HTMLResponse,
    status_code=status.HTTP_200_OK,
)
async def put_assign_athlete_team_leader(
    request: Request,
    competitor_id: int,
    tl_c: Annotated[str, Form()],
    db_session: db_dependency,
) -> HTMLResponse:
    user = authenticate_request(request)
    if not user:
        raise unauthorised_exception()

    await assign_athlete_team_role(db_session=db_session, competitor_id=competitor_id, tl_c=tl_c)

    return HTMLResponse(content=f"<td>{tl_c}</td>")


@athlete_router.put("/rename_team/{team_name_current}", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def put_rename_team(
    request: Request,
    team_name_current: str,
    team_name_new: Annotated[str, Form()],
    db_session: db_dependency,
) -> None:
    user = authenticate_request(request)
    if not user:
        raise unauthorised_exception()

    await rename_team(db_session=db_session, team_name_current=team_name_current, team_name_new=team_name_new)
