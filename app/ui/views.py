from __future__ import annotations

from fastapi import APIRouter, Request, Response, status
from fastapi.responses import HTMLResponse

from app.appreciation.views import appreciation_router
from app.athlete.views import athlete_router
from app.athlete_prefs.views import athlete_prefs_router
from app.attendance.views import attendance_router
from app.auth.views import auth_router
from app.cf_games.views import cf_games_router
from app.score.views import score_router
from app.ui.template import templates

router = APIRouter()


@router.get("/", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def get_home_landing_page(request: Request) -> Response:
    return templates.TemplateResponse(
        request=request,
        name="pages/home.jinja2",
    )


@router.get("/refresh_button", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def get_ui_refresh_button(request: Request) -> Response:
    return templates.TemplateResponse(
        request=request,
        name="partials/refresh_btn.jinja2",
    )


router.include_router(auth_router)
router.include_router(cf_games_router)
router.include_router(athlete_router)
router.include_router(score_router)
router.include_router(attendance_router)
router.include_router(appreciation_router)
router.include_router(athlete_prefs_router)
