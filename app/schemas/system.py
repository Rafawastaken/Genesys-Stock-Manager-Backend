# app/schemas/system.py
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class HealthDTO(BaseModel):
    ok: bool
    status: Literal["ok", "degraded", "down"]
    env: str
    now: str
    uptime_s: float | None
    db_ok: bool

    # opcionais (novo)
    request_id: str | None = None
    version: str | None = None
    service: str | None = None
    started_at: str | None = None
    db_latency_ms: float | None = None
