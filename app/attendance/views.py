from __future__ import annotations

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Form, Request, Response, status
from fastapi.responses import HTMLResponse

from app.attendance.models import Attendance
from app.attendance.service import get_athlete_attendance_data
from app.auth.service import authenticate_request
from app.database.dependencies import db_dependency
from app.exceptions import unauthorised_exception
from app.ui.template import templates

log = logging.getLogger("uvicorn.error")

attendance_router = APIRouter()


@attendance_router.get("/attendance", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def get_attendance_page(request: Request, _: db_dependency) -> Response:
    user = authenticate_request(request)
    if not user:
        raise unauthorised_exception()

    return templates.TemplateResponse(
        request=request,
        name="pages/attendance.jinja2",
    )


@attendance_router.post("/athlete_attendance", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def get_athlete_attendance_table(
    request: Request,
    db_session: db_dependency,
    name: Annotated[str, Form()],
) -> Response:
    user = authenticate_request(request)
    if not user:
        raise unauthorised_exception()

    attendance = await get_athlete_attendance_data(db_session=db_session)
    filtered_attendance = {k: v for k, v in attendance.items() if name.casefold() in v.get("name", "").casefold()}
    return templates.TemplateResponse(
        request=request,
        name="partials/athlete_attendance_tbody.jinja2",
        context={
            "attendance": filtered_attendance,
        },
    )


@attendance_router.post(
    "/attendance/{athlete_id}/{ordinal}",
    response_class=HTMLResponse,
    status_code=status.HTTP_200_OK,
)
async def post_create_new_attendance_record(
    request: Request,
    db_session: db_dependency,
    athlete_id: UUID,
    ordinal: int,
) -> Response:
    user = authenticate_request(request)
    if not user:
        raise unauthorised_exception()

    attendance = await Attendance.find(async_session=db_session, athlete_id=athlete_id, ordinal=ordinal)
    if not attendance:
        await Attendance(athlete_id=athlete_id, ordinal=ordinal).save(async_session=db_session)

    return templates.TemplateResponse(
        request=request,
        name="partials/athlete_attendance_td_delete.jinja2",
        context={
            "id": athlete_id,
            "ordinal": ordinal,
        },
    )


@attendance_router.delete(
    "/attendance/{athlete_id}/{ordinal}",
    response_class=HTMLResponse,
    status_code=status.HTTP_200_OK,
)
async def delete_attendance_record(
    request: Request,
    db_session: db_dependency,
    athlete_id: UUID,
    ordinal: int,
) -> Response:
    user = authenticate_request(request)
    if not user:
        raise unauthorised_exception()

    attendance = await Attendance.find(async_session=db_session, athlete_id=athlete_id, ordinal=ordinal)
    if attendance:
        await attendance.delete(async_session=db_session)

    return templates.TemplateResponse(
        request=request,
        name="partials/athlete_attendance_td_post.jinja2",
        context={
            "id": athlete_id,
            "ordinal": ordinal,
        },
    )
