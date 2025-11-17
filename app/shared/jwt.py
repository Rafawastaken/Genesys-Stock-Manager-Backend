from datetime import UTC, datetime, timedelta
from typing import Any, TypedDict

import jwt

from app.core.config import settings

ALGO = "HS256"


class DecodedToken(TypedDict, total=False):
    sub: str
    role: str
    name: str
    typ: str
    exp: int
    iat: int


def _now_utc() -> datetime:
    return datetime.now(UTC)


def _encode(payload: dict[str, Any], minutes: int) -> str:
    now = _now_utc()
    exp = now + timedelta(minutes=minutes)
    to_encode = {"iat": int(now.timestamp()), "exp": int(exp.timestamp()), **payload}
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=ALGO)


def create_access_token(*, sub: str, role: str, name: str | None = None) -> str:
    payload: dict[str, Any] = {"sub": sub, "role": role, "typ": "access"}
    if name is not None:
        payload["name"] = name
    return _encode(payload, settings.JWT_EXPIRE_MIN)


def create_refresh_token(*, sub: str, role: str, name: str | None = None) -> str:
    # inclui name também para conseguirmos reproduzir no novo access durante refresh
    payload: dict[str, Any] = {"sub": sub, "role": role, "typ": "refresh"}
    if name is not None:
        payload["name"] = name
    return _encode(payload, settings.JWT_REFRESH_EXPIRE_MIN)


def decode_token(token: str, *, expected_typ: str | None = None) -> DecodedToken:
    data = jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGO])
    if expected_typ and data.get("typ") != expected_typ:
        raise jwt.InvalidTokenError(f"invalid token typ: {data.get('typ')}")
    return data  # type: ignore[return-value]
