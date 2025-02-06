import logging
from collections.abc import Sequence
from typing import Any

from fastapi import APIRouter, status

from app.cf_games.constants import AFFILIATE_ID, YEAR
from app.database.dependencies import db_dependency
from app.score.models import Score
from app.score.schemas import ScoreBaseModel
from app.score.service import get_team_scores, update_ranks

log = logging.getLogger("uvicorn.error")

score_router = APIRouter(prefix="/score", tags=["score"])


@score_router.get("/scores", response_model=list[ScoreBaseModel], status_code=status.HTTP_200_OK)
async def get_team_scores(
    db_session: db_dependency,
    ordinal: int,
    year: int = int(YEAR),
    affiliate_id: int = int(AFFILIATE_ID),
) -> Sequence[Score]:
    return await get_team_scores(db_session=db_session, year=year, affiliate_id=affiliate_id, ordinal=ordinal)


@score_router.get("/rank", status_code=status.HTTP_200_OK, response_model=None)
async def get_ranks(
    db_session: db_dependency,
    year: int = int(YEAR),
    affiliate_id: int = int(AFFILIATE_ID),
) -> Sequence[Any]:
    return await update_ranks(db_session=db_session, ordinal=1, affiliate_id=affiliate_id, year=year)
