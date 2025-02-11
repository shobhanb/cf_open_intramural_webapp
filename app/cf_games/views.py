import logging

from fastapi import APIRouter, Request, status
from fastapi.responses import RedirectResponse

from app.auth.service import authenticate_request
from app.cf_games.constants import AFFILIATE_ID, YEAR
from app.cf_games.service import process_cf_data
from app.database.dependencies import db_dependency
from app.exceptions import unauthorised_exception

log = logging.getLogger("uvicorn.error")

cf_games_router = APIRouter()


@cf_games_router.get("/refresh", status_code=status.HTTP_200_OK)
async def refresh_cf_games_data(
    request: Request,
    db_session: db_dependency,
    year: int = int(YEAR),
    affiliate_id: int = int(AFFILIATE_ID),
) -> RedirectResponse:
    user = authenticate_request(request)
    if user:
        await process_cf_data(db_session=db_session, affiliate_id=affiliate_id, year=year)
        return RedirectResponse("/")
    raise unauthorised_exception()
