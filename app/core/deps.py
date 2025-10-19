# app/core/deps.py
# Dependências comuns para rotas FastAPI

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

import logging

from app.shared.jwt import decode_token
from app.shared.jwt import decode_token
from app.infra.session import get_session
from app.infra.uow import UoW


log = logging.getLogger("gsm.core.deps")

_auth = HTTPBearer(auto_error=True)


def require_access_token(creds: HTTPAuthorizationCredentials = Depends(_auth)):
    try:
        return decode_token(creds.credentials, expected_typ="access")
    except Exception as e:
        log.error("Error refreshing token: %s", e)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido ou expirado")

def get_uow(db: Session = Depends(get_session)) -> UoW:
    return UoW(db)
