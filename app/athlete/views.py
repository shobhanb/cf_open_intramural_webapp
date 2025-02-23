from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Form, Request, Response, status
from fastapi.responses import HTMLResponse

from app.athlete.models import Athlete
from app.athlete.service import (
    assign_athlete_to_team,
    get_athlete_teams_dict,
    get_athlete_teams_list,
    get_team_composition_dict,
    get_team_names,
    random_assign_zz_athlete,
    rename_team,
)
from app.auth.service import authenticate_request
from app.cf_games.constants import TEAM_LEADER_REVERSE_MAP
from app.database.dependencies import db_dependency
from app.exceptions import not_found_exception, unauthorised_exception
from app.ui.template import templates

log = logging.getLogger("uvicorn.error")

athlete_router = APIRouter()


@athlete_router.get("/team_members", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def get_team_members(request: Request, db_session: db_dependency) -> Response:
    teams = await get_athlete_teams_dict(db_session=db_session)
    team_composition = await get_team_composition_dict(db_session=db_session)
    team_composition_totals = {k: sum([x.get("count", 0) for x in v]) for k, v in team_composition.items()}
    return templates.TemplateResponse(
        request=request,
        name="pages/team_members.jinja2",
        context={
            "teams": teams,
            "team_composition": team_composition,
            "team_composition_totals": team_composition_totals,
        },
    )


@athlete_router.get("/assign_teams", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def get_manual_teams_assign_page(request: Request, _: db_dependency) -> Response:
    user = authenticate_request(request)
    if not user:
        raise unauthorised_exception()

    return templates.TemplateResponse(
        request=request,
        name="pages/manual_team_assign.jinja2",
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


@athlete_router.get(
    "/athlete_team_assignment/{competitor_id}",
    response_class=HTMLResponse,
    status_code=status.HTTP_200_OK,
)
async def get_athlete_team_assign_partial(competitor_id: int, request: Request, db_session: db_dependency) -> Response:
    user = authenticate_request(request)
    if not user:
        raise unauthorised_exception()

    athlete = await Athlete.find_or_raise(async_session=db_session, competitor_id=competitor_id)
    return templates.TemplateResponse(
        request=request,
        name="partials/athlete_team_assign_form.jinja2",
        context={
            "athlete": athlete,
        },
    )


@athlete_router.post("/athlete_teams_tbody", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
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
    team_name_new: Annotated[str, Form()],
    tl_c: Annotated[str, Form()],
    db_session: db_dependency,
) -> Response:
    user = authenticate_request(request)
    if not user:
        raise unauthorised_exception()

    await assign_athlete_to_team(db_session=db_session, competitor_id=competitor_id, team_name=team_name_new, tl_c=tl_c)

    return templates.TemplateResponse(
        request=request,
        name="partials/done.jinja2",
        context={
            "url": "/assign_teams",
        },
    )


@athlete_router.put("/rename_team/{team_name_current}", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def put_rename_team(
    request: Request,
    team_name_current: str,
    team_name_new: Annotated[str, Form()],
    db_session: db_dependency,
) -> Response:
    user = authenticate_request(request)
    if not user:
        raise unauthorised_exception()

    if team_name_new == "":
        raise not_found_exception()

    await rename_team(db_session=db_session, team_name_current=team_name_current, team_name_new=team_name_new)

    teams = await get_team_names(db_session=db_session)
    return templates.TemplateResponse(
        request=request,
        name="pages/rename_teams.jinja2",
        context={
            "teams": teams,
        },
    )


@athlete_router.post("/auto_assign_teams", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def post_auto_assign_teams(
    request: Request,
    db_session: db_dependency,
) -> Response:
    user = authenticate_request(request)
    if not user:
        raise unauthorised_exception()

    await random_assign_zz_athlete(db_session=db_session)

    return templates.TemplateResponse(
        request=request,
        name="partials/done.jinja2",
        context={
            "url": "/team_members",
        },
    )
