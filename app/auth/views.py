import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm

from app.auth.service import (
    add_item_to_header,
    create_access_token,
    create_refresh_token,
    verify_admin_username_password,
)
from app.ui.template import templates

log = logging.getLogger("uvicorn.error")

auth_router = APIRouter()


@auth_router.get("/login")
async def get_login_form(
    request: Request,
) -> Response:
    return templates.TemplateResponse(
        request=request,
        name="pages/login_form.jinja2",
    )


@auth_router.post("/login")
async def login_for_access_token(
    request: Request,
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Response:
    if verify_admin_username_password(username=form_data.username, password=form_data.password):
        request = add_item_to_header(request, "rjtc_admin", form_data.username)

        data = {"sub": form_data.username}
        access_token = create_access_token(data=data)
        refresh_token = create_refresh_token(data=data)

        response = templates.TemplateResponse(request=request, name="partials/auth_success.jinja2")
        response.set_cookie(key="access_token", value=access_token, httponly=True, samesite="lax")
        response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, samesite="lax")
        return response

    return templates.TemplateResponse(request=request, name="partials/auth_fail.jinja2")


@auth_router.get("/logout")
async def logout() -> RedirectResponse:
    response = RedirectResponse(url="/")
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    return response
