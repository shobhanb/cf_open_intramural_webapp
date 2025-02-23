from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Callable

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles

from app.auth.service import add_item_to_header, create_access_token, verify_token
from app.database.base import Base
from app.database.engine import session_manager
from app.ui.template import templates
from app.ui.views import router

RESET_DB = False


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator:
    # Run pre-load stuff
    if RESET_DB:
        async with session_manager.connect() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(router)
app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=5)


@app.get("/health")
async def health_check() -> dict:
    return {"status": "Ok"}


@app.exception_handler(status.HTTP_404_NOT_FOUND)
@app.exception_handler(status.HTTP_403_FORBIDDEN)
@app.exception_handler(status.HTTP_401_UNAUTHORIZED)
@app.exception_handler(HTTPException)
async def custom_404_handler(request: Request, __) -> Response:  # noqa: ANN001
    return await get_404(request=request)


async def get_404(request: Request) -> Response:
    response = templates.TemplateResponse(
        request=request,
        name="pages/404.jinja2",
    )
    response.headers["HX-Retarget"] = "body"
    response.headers["HX-Reswap"] = "innerhtml"
    return response


@app.middleware("http")
async def add_admin_headers(request: Request, call_next: Callable) -> Response:
    access_token = request.cookies.get("access_token")
    if access_token:
        access_token_data = verify_token(access_token)
        if access_token_data:
            request = add_item_to_header(request=request, key="rjtc_admin", value=access_token_data.username)  # type: ignore  # noqa: PGH003
            return await call_next(request)

    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        refresh_token_data = verify_token(refresh_token)
        if refresh_token_data:
            new_access_token = create_access_token({"sub": refresh_token_data.username})
            request = add_item_to_header(request=request, key="rjtc_admin", value=refresh_token_data.username)  # type: ignore  # noqa: PGH003
            response = await call_next(request)
            response.set_cookie(key="access_token", value=new_access_token, httponly=True, samesite="lax")
            return response

    return await call_next(request)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
