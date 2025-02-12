from typing import Any

import jinja_partials
from fastapi import Request
from fastapi.templating import Jinja2Templates

from app.cf_games.constants import RENDER_CONTEXT


def get_render_context(request: Request) -> dict[str, Any]:
    return {"info": RENDER_CONTEXT}


templates = Jinja2Templates(directory="templates", context_processors=[get_render_context])

jinja_partials.register_starlette_extensions(templates=templates)
