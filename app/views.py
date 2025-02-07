from fastapi import APIRouter, status
from fastapi.responses import RedirectResponse

from app.athlete.views import athlete_router
from app.auth.views import auth_router
from app.cf_games.views import cf_games_router
from app.score.views import score_router
from app.ui.views import ui_router

router = APIRouter()


router.include_router(auth_router)
router.include_router(cf_games_router)
router.include_router(athlete_router)
router.include_router(score_router)
router.include_router(ui_router)


@router.get("/", response_class=RedirectResponse, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
async def team_scores_redirect() -> RedirectResponse:
    return RedirectResponse(url="/team_members")
