from fastapi import APIRouter, Depends
from app.schemas.auth import LoginRequest, LoginResponse
from app.services.commands.auth.login import login
from app.core.deps import require_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=LoginResponse)
def post_login(body: LoginRequest):
    return login(body)

@router.get("/me")
def get_me(user = Depends(require_access_token)):
    return {"user": user}
