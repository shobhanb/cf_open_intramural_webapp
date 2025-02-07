from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Callable

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.auth.service import verify_token
from app.cf_games.constants import RENDER_CONTEXT
from app.database.base import Base
from app.database.engine import session_manager
from app.template import templates
from app.views import router

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


@app.get("/health")
async def health_check() -> dict:
    return {"status": "Ok"}


@app.exception_handler(404)
@app.exception_handler(401)
async def custom_404_handler(request: Request, __) -> HTMLResponse:  # noqa: ANN001
    return await get_404(request=request)


async def get_404(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="pages/404.jinja2",
        context={"info": RENDER_CONTEXT, "admin": False},
    )


@app.middleware("http")
async def add_admin_headers(request: Request, call_next: Callable) -> Response:
    token = request.cookies.get("access_token")
    response = await call_next(request)
    if token:
        user = verify_token(token)
        if user:
            response.headers["X-Admin"] = "admin"
    return response


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
