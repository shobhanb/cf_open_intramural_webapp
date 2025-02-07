import logging

from fastapi import APIRouter, Request, status
from fastapi.responses import HTMLResponse

from app.athlete.service import get_athlete_teams
from app.database.dependencies import db_dependency
from app.template import templates

log = logging.getLogger("uvicorn.error")

ADMIN = True

athlete_router = APIRouter()


@athlete_router.get("/team_members", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def get_team_members(request: Request, db_session: db_dependency) -> HTMLResponse:
    teams = await get_athlete_teams(db_session=db_session)
    return templates.TemplateResponse(
        request=request,
        name="pages/team_members.jinja2",
        context={
            "teams": teams,
            "admin": False,
        },
    )
