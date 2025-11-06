# app/schemas/system.py
from __future__ import annotations
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel

class HealthDTO(BaseModel):
    ok: bool
    status: Literal["ok", "degraded", "down"]
    env: str
    now: str
    uptime_s: Optional[float]
    db_ok: bool

    # opcionais (novo)
    request_id: Optional[str] = None
    version: Optional[str] = None
    service: Optional[str] = None
    started_at: Optional[str] = None
    db_latency_ms: Optional[float] = None
