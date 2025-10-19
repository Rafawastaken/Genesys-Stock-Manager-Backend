# app/schemas/system.py
# Esquema Pydantic para o DTOs de sistema.

from pydantic import BaseModel
from typing import Optional

class HealthDTO(BaseModel):
    ok: bool
    status: str
    service: str = "backend"
    env: str
    now: str
    uptime_s: Optional[float] = None
    db_ok: Optional[bool] = None
