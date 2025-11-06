# app/domains/auth/usecases/login.py

from __future__ import annotations

from fastapi import HTTPException, status

from app.core.config import settings
from app.external.prestashop_client import PrestashopClient
from app.schemas.auth import LoginRequest, LoginResponse
from app.shared.jwt import create_access_token


def execute(req: LoginRequest) -> LoginResponse:
    """
    Authenticate against Prestashop and issue a JWT access token.
    Errors are always in English.
    """
    client = PrestashopClient()
    try:
        user = client.login(req.email, req.password)
    except Exception as err:
        # Keep it generic to avoid leaking auth details
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        ) from err

    access = create_access_token(
        sub=str(user["id"]),
        role=user.get("role", "user"),
        name=user.get("name"),
    )
    expires_in = int(getattr(settings, "JWT_EXPIRE_MIN", 120)) * 60

    return LoginResponse(
        access_token=access,
        expires_in=expires_in,
        user={
            "uid": user["id"],
            "email": user["email"],
            "name": user.get("name"),
            "role": user.get("role", "user"),
        },
    )
