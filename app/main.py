from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.cf_games.views import cf_games_router
from app.database.base import Base
from app.database.engine import session_manager
from app.template_views import template_router

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

app.include_router(cf_games_router)
app.include_router(template_router)


@app.get("/health")
async def health_check() -> dict:
    return {"status": "Ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
