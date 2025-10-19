# app/api/v1/system.py
from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings
from app.infra.session import get_session          # 👈 trocar aqui
from app.schemas.system import HealthDTO

router = APIRouter(tags=["health"])

@router.get("/healthz", response_model=HealthDTO)
def healthz(request: Request, db: Session = Depends(get_session)):   # 👈 e aqui
    tz = ZoneInfo(settings.TIMEZONE)
    now = datetime.now(tz)

    started_at = getattr(request.app.state, "started_at", None)
    uptime_s = (now - started_at).total_seconds() if started_at else None

    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    return HealthDTO(
        ok=True,
        status="ok" if db_ok else "degraded",
        env=settings.APP_ENV,
        now=now.isoformat(),
        uptime_s=uptime_s,
        db_ok=db_ok,
    )
