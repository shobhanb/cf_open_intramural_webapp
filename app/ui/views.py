from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.ui.template import templates

ui_router = APIRouter(prefix="/ui")


@ui_router.get("/refresh_button")
async def get_ui_refresh_button(request: Request) -> Response:
    return templates.TemplateResponse(
        request=request,
        name="partials/refresh_btn.jinja2",
    )
