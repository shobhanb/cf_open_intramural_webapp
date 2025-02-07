from typing import Any

from fastapi import Request
from fastapi.templating import Jinja2Templates

from app.cf_games.constants import RENDER_CONTEXT


def get_render_context(request: Request) -> dict[str, Any]:
    return {"app": request.app, "info": RENDER_CONTEXT}


templates = Jinja2Templates(directory="templates", context_processors=[get_render_context])
