import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm

from app.auth.exceptions import unauthorised_exception
from app.auth.service import create_access_token, verify_admin_username_password
from app.template import templates

log = logging.getLogger("uvicorn.error")

auth_router = APIRouter()


@auth_router.get("/login")
async def get_login_form(
    request: Request,
) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="pages/login_form.jinja2",
    )


@auth_router.post("/login")
async def login_for_access_token(
    request: Request,
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> HTMLResponse:
    if verify_admin_username_password(username=form_data.username, password=form_data.password):
        data = {"sub": form_data.username}
        access_token = create_access_token(data=data)
        response = templates.TemplateResponse(
            request=request,
            name="partials/auth_response.jinja2",
        )
        response.set_cookie(key="access_token", value=access_token, httponly=True, samesite="lax")
        return response
    raise unauthorised_exception()


@auth_router.get("/logout")
async def logout(
    request: Request,
) -> RedirectResponse:
    response = RedirectResponse(url="/")
    response.delete_cookie(key="access_token")
    return response
