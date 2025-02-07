from typing import Any

from fastapi import Request
from fastapi.templating import Jinja2Templates

from app.cf_games.constants import RENDER_CONTEXT


def render_context(_: Request) -> dict[str, Any]:
    return {"info": RENDER_CONTEXT}


templates = Jinja2Templates(directory="templates", context_processors=[render_context])
