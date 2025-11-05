from fastapi import APIRouter, Depends
from app.schemas.auth import LoginRequest, LoginResponse
from app.domains.auth.usecases.login import execute as uc_login
from app.core.deps import require_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=LoginResponse)
def post_login(body: LoginRequest):
    return uc_login(body)

@router.get("/me")
def get_me(user = Depends(require_access_token)):
    return {"user": user}
