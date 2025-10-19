from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, TypedDict
import jwt
from app.core.config import settings

ALGO = "HS256"

class DecodedToken(TypedDict, total=False):
    sub: str
    role: str
    name: str            # ← agora suportado
    typ: str
    exp: int
    iat: int

def _now_utc() -> datetime:
    return datetime.now(timezone.utc)

def _encode(payload: Dict[str, Any], minutes: int) -> str:
    now = _now_utc()
    exp = now + timedelta(minutes=minutes)
    to_encode = {"iat": int(now.timestamp()), "exp": int(exp.timestamp()), **payload}
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=ALGO)

def create_access_token(*, sub: str, role: str, name: str | None = None) -> str:
    payload: Dict[str, Any] = {"sub": sub, "role": role, "typ": "access"}
    if name is not None:
        payload["name"] = name
    return _encode(payload, settings.JWT_EXPIRE_MIN)

def create_refresh_token(*, sub: str, role: str, name: str | None = None) -> str:
    # inclui name também para conseguirmos reproduzir no novo access durante refresh
    payload: Dict[str, Any] = {"sub": sub, "role": role, "typ": "refresh"}
    if name is not None:
        payload["name"] = name
    return _encode(payload, settings.JWT_REFRESH_EXPIRE_MIN)

def decode_token(token: str, *, expected_typ: Optional[str] = None) -> DecodedToken:
    data = jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGO])
    if expected_typ and data.get("typ") != expected_typ:
        raise jwt.InvalidTokenError(f"invalid token typ: {data.get('typ')}")
    return data  # type: ignore[return-value]
