from fastapi import APIRouter

from app.cf_games.views import cf_games_router

router = APIRouter()


router.include_router(cf_games_router)
# router.include_router(athlete_router)
# router.include_router(score_router)
