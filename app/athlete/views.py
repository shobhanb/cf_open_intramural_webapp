import logging
from collections.abc import Sequence

from fastapi import APIRouter, status

from app.athlete.models import Athlete
from app.athlete.schemas import AthleteBaseModel
from app.cf_games.constants import AFFILIATE_ID, YEAR
from app.database.dependencies import db_dependency

log = logging.getLogger("uvicorn.error")

athlete_router = APIRouter(prefix="/athlete", tags=["athlete"])


@athlete_router.get("/all", response_model=list[AthleteBaseModel], status_code=status.HTTP_200_OK)
async def get_all_athletes(
    db_session: db_dependency,
    year: int = int(YEAR),
    affiliate_id: int = int(AFFILIATE_ID),
) -> Sequence[Athlete]:
    return await Athlete.find_all(db_session, affiliate_id=affiliate_id, year=year)
