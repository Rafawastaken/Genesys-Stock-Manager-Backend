import logging
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.shared.jwt import decode_token

log = logging.getLogger("gsm.core.deps.auth")
_auth = HTTPBearer(auto_error=True)


def require_access_token(creds: Annotated[HTTPAuthorizationCredentials, Depends(_auth)]):
    try:
        return decode_token(creds.credentials, expected_typ="access")
    except Exception as e:
        log.error("Invalid/expired token: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido ou expirado"
        ) from e
