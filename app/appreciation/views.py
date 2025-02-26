from __future__ import annotations

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Form, Request, Response, status
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.appreciation.models import Appreciation
from app.athlete.models import Athlete
from app.auth.service import authenticate_request
from app.cf_games.constants import DEFAULT_APPRECIATION_SCORE
from app.database.dependencies import db_dependency
from app.exceptions import unauthorised_exception
from app.ui.template import templates

log = logging.getLogger("uvicorn.error")

appreciation_router = APIRouter()


@appreciation_router.get("/appreciation", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def get_appreciation_page(request: Request, db_session: db_dependency) -> Response:
    user = authenticate_request(request)
    if not user:
        raise unauthorised_exception()

    return await return_partial_appreciation_table(
        request=request,
        db_session=db_session,
        template_name="pages/appreciation.jinja2",
    )


@appreciation_router.post(
    "/appreciation",
    response_class=HTMLResponse,
    status_code=status.HTTP_200_OK,
)
async def post_create_appreciation_record(
    request: Request,
    db_session: db_dependency,
    athlete_id: Annotated[UUID, Form()],
    ordinal: Annotated[int, Form()],
    score: Annotated[int, Form()],
) -> Response:
    user = authenticate_request(request)
    if not user:
        raise unauthorised_exception()

    appreciation = await Appreciation.find(async_session=db_session, athlete_id=athlete_id, ordinal=ordinal)
    if not appreciation:
        appreciation = Appreciation(athlete_id=athlete_id, ordinal=ordinal)

    appreciation.score = score
    db_session.add(appreciation)
    await db_session.commit()

    return await return_partial_appreciation_table(
        request=request,
        db_session=db_session,
        template_name="partials/appreciation_table.jinja2",
    )


@appreciation_router.delete(
    "/appreciation/{athlete_id}/{ordinal}",
    response_class=HTMLResponse,
    status_code=status.HTTP_200_OK,
)
async def delete_appreciation_record(
    request: Request,
    db_session: db_dependency,
    athlete_id: UUID,
    ordinal: int,
) -> Response:
    user = authenticate_request(request)
    if not user:
        raise unauthorised_exception()

    appreciation = await Appreciation.find(async_session=db_session, athlete_id=athlete_id, ordinal=ordinal)
    if appreciation:
        await appreciation.delete(async_session=db_session)

    return await return_partial_appreciation_table(
        request=request,
        db_session=db_session,
        template_name="partials/appreciation_table.jinja2",
    )


async def return_partial_appreciation_table(
    request: Request,
    db_session: AsyncSession,
    template_name: str,
) -> Response:
    appreciation_stmt = (
        select(Appreciation.athlete_id, Appreciation.ordinal, Appreciation.event_name, Appreciation.score, Athlete.name)
        .join_from(Appreciation, Athlete, Appreciation.athlete_id == Athlete.id)
        .order_by(Appreciation.ordinal, Athlete.name)
    )
    result = await db_session.execute(appreciation_stmt)
    appreciation = result.mappings().all()

    athlete_stmt = select(Athlete.name, Athlete.id).order_by(Athlete.name)
    result = await db_session.execute(athlete_stmt)
    athletes = result.mappings().all()

    return templates.TemplateResponse(
        request=request,
        name=template_name,
        context={
            "appreciation": appreciation,
            "athletes": athletes,
            "default_score": DEFAULT_APPRECIATION_SCORE,
        },
    )
