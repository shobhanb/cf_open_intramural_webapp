from __future__ import annotations

from fastapi import APIRouter, Request, Response, status
from fastapi.responses import HTMLResponse

from app.ui.template import templates

ui_router = APIRouter()


@ui_router.get("/", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def get_home_landing_page(request: Request) -> Response:
    return templates.TemplateResponse(
        request=request,
        name="pages/home.jinja2",
    )


@ui_router.get("/refresh_button", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def get_ui_refresh_button(request: Request) -> Response:
    return templates.TemplateResponse(
        request=request,
        name="partials/refresh_btn.jinja2",
    )
