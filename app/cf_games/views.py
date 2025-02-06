import logging

from fastapi import APIRouter, status

from app.cf_games.constants import AFFILIATE_ID, YEAR
from app.cf_games.schemas import CFDataCountModel
from app.cf_games.service import process_cf_data
from app.database.dependencies import db_dependency

log = logging.getLogger("uvicorn.error")

cf_games_router = APIRouter(prefix="/cf_games", tags=["cf_games"])


@cf_games_router.put("/refresh", status_code=status.HTTP_200_OK)
async def refresh_cf_games_data(
    db_session: db_dependency,
    year: int = int(YEAR),
    affiliate_id: int = int(AFFILIATE_ID),
) -> CFDataCountModel:
    return await process_cf_data(db_session=db_session, affiliate_id=affiliate_id, year=year)
