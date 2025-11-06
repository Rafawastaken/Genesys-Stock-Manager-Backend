from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.deps import require_access_token
from app.domains.auth.usecases.login import execute as uc_login
from app.schemas.auth import LoginRequest, LoginResponse

router = APIRouter(prefix="/auth", tags=["auth"])
UserDep = Annotated[dict, Depends(require_access_token)]


@router.post("/login", response_model=LoginResponse)
def post_login(body: LoginRequest):
    return uc_login(body)


@router.get("/me")
def get_me(user: UserDep):
    return {"user": user}
