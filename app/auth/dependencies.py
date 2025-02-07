from typing import Annotated

from fastapi import Depends

from app.auth.service import authenticate

admin_dependency = Annotated[bool, Depends(authenticate)]
