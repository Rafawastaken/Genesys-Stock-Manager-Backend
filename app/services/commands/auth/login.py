# app/services/commands/auth/login.py
# Serviço de login que autentica um utilizador via Prestashop e emite um token JWT.

from fastapi import HTTPException, status
from app.external.prestashop_client import PrestashopClient
from app.schemas.auth import LoginRequest, LoginResponse
from app.shared.jwt import create_access_token  # podes também emitir refresh se quiseres
from app.core.config import settings

def login(req: LoginRequest) -> LoginResponse:
    client = PrestashopClient()
    try:
        user = client.login(req.email, req.password)
    except Exception as e:
        # Logar e devolver 401 genérico
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas")

    access = create_access_token(sub=str(user["id"]), role=user.get("role", "user"), name=user.get("name"))
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
