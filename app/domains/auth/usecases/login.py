# app/domains/auth/usecases/login.py
from __future__ import annotations
from typing import Any
from collections.abc import Callable

from app.core.config import settings
from app.core.errors import Unauthorized
from app.schemas.auth import LoginRequest, LoginResponse
from app.shared.jwt import create_access_token

AuthFn = Callable[[str, str], dict[str, Any]]


def execute(req: LoginRequest, *, auth_login: AuthFn) -> LoginResponse:
    """
    Authenticate via injected auth function and issue a JWT.
    Keep domain pure: no HTTPException, no external clients here.
    """
    try:
        user = auth_login(req.email, req.password)
    except Exception as err:
        # genérico para não vazar detalhes
        raise Unauthorized("Invalid credentials") from err

    access = create_access_token(
        sub=str(user.get("id")),
        role=user.get("role", "user"),
        name=user.get("name"),
    )
    expires_in = int(getattr(settings, "JWT_EXPIRE_MIN", 120)) * 60

    return LoginResponse(
        access_token=access,
        expires_in=expires_in,
        user={
            "uid": user.get("id"),
            "email": user.get("email"),
            "name": user.get("name"),
            "role": user.get("role", "user"),
        },
    )
