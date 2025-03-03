from __future__ import annotations

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Form, Request, Response, status
from fastapi.responses import HTMLResponse
from sqlalchemy import delete, select, update

from app.athlete.models import Athlete
from app.athlete_prefs.constants import RX_PREFS, TIME_PREFS
from app.athlete_prefs.models import AthleteRXPref, AthleteTimePref
from app.athlete_prefs.schemas import AthletePrefsModel
from app.athlete_prefs.service import get_athlete_prefs_data_dump
from app.cf_games.constants import IGNORE_TEAMS
from app.database.dependencies import db_dependency
from app.exceptions import not_found_exception
from app.ui.template import templates

log = logging.getLogger("uvicorn.error")

athlete_prefs_router = APIRouter()


@athlete_prefs_router.get("/athlete_prefs_page", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def get_athlete_prefs_page(request: Request, db_session: db_dependency) -> Response:
    stmt = select(Athlete.id, Athlete.name).where(Athlete.team_name.not_in(IGNORE_TEAMS)).order_by(Athlete.name)
    ret = await db_session.execute(stmt)
    athletes = ret.mappings().all()

    return templates.TemplateResponse(
        request=request,
        name="pages/athlete_prefs.jinja2",
        context={
            "athletes": athletes,
            "allowed_times": TIME_PREFS,
        },
    )


@athlete_prefs_router.post("/athlete_prefs", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def post_athlete_prefs_get_table(
    request: Request,
    db_session: db_dependency,
    athlete_id: Annotated[UUID, Form()],
) -> Response:
    stmt = select(AthleteRXPref).where(AthleteRXPref.athlete_id == athlete_id)
    ret = await db_session.execute(stmt)
    rx_pref = ret.scalars().first()

    stmt = (
        select(AthleteTimePref).where(AthleteTimePref.athlete_id == athlete_id).order_by(AthleteTimePref.preference_nbr)
    )
    ret = await db_session.execute(stmt)
    time_prefs = ret.scalars().all()

    return templates.TemplateResponse(
        request=request,
        name="partials/athlete_prefs_table.jinja2",
        context={
            "rx_pref": rx_pref,
            "time_prefs": time_prefs,
            "allowed_rx": RX_PREFS,
            "allowed_times": TIME_PREFS,
        },
    )


@athlete_prefs_router.put("/athlete_prefs/rx/{athlete_id}", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def put_change_athlete_rx_pref(
    request: Request,
    db_session: db_dependency,
    athlete_id: UUID,
    new_rx_pref: Annotated[str, Form()],
) -> Response:
    if new_rx_pref in RX_PREFS:
        stmt = update(AthleteRXPref).where(AthleteRXPref.athlete_id == athlete_id).values(rx_pref=new_rx_pref)
        await db_session.execute(stmt)
        await db_session.commit()

    stmt = select(AthleteRXPref).where(AthleteRXPref.athlete_id == athlete_id)
    ret = await db_session.execute(stmt)
    rx_pref = ret.scalars().first()

    return templates.TemplateResponse(
        request=request,
        name="partials/athlete_prefs_rx_table.jinja2",
        context={
            "rx_pref": rx_pref,
            "allowed_rx": RX_PREFS,
        },
    )


@athlete_prefs_router.put(
    "/athlete_prefs/time/{athlete_id}",
    response_class=HTMLResponse,
    status_code=status.HTTP_200_OK,
)
async def put_change_athlete_time_pref(
    request: Request,
    db_session: db_dependency,
    athlete_id: UUID,
    time_pref: Annotated[list[str], Form()],
) -> Response:
    if set(time_pref) != set(TIME_PREFS):
        raise not_found_exception()

    delete_stmt = delete(AthleteTimePref).where(AthleteTimePref.athlete_id == athlete_id)
    await db_session.execute(delete_stmt)

    for idx, pref in enumerate(time_pref):
        record = AthleteTimePref(athlete_id=athlete_id, preference_nbr=idx, preference=pref)
        db_session.add(record)

    await db_session.commit()

    stmt = (
        select(AthleteTimePref).where(AthleteTimePref.athlete_id == athlete_id).order_by(AthleteTimePref.preference_nbr)
    )
    ret = await db_session.execute(stmt)
    time_prefs = ret.scalars().all()

    return templates.TemplateResponse(
        request=request,
        name="partials/athlete_prefs_time_table.jinja2",
        context={
            "time_prefs": time_prefs,
            "allowed_times": TIME_PREFS,
        },
    )


@athlete_prefs_router.get("/athlete_prefs/data")
async def get_athlete_prefs_download(
    db_session: db_dependency,
) -> list[AthletePrefsModel]:
    prefs = await get_athlete_prefs_data_dump(db_session=db_session)
    return [AthletePrefsModel.model_validate(x) for x in prefs]
