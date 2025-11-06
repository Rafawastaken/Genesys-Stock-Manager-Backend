# app/api/v1/system.py
import time
from datetime import datetime
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_request_id  # já tens no teu core.logging
from app.infra.session import get_session
from app.schemas.system import HealthDTO

router = APIRouter(tags=["health"])
SessionDep = Annotated[Session, Depends(get_session)]


@router.get("/healthz", response_model=HealthDTO)
def healthz(request: Request, response: Response, db: SessionDep):
    tz = ZoneInfo(settings.TIMEZONE)
    now_dt = datetime.now(tz)
    now = now_dt.isoformat()

    started_at_dt = getattr(request.app.state, "started_at", None)
    uptime_s = (now_dt - started_at_dt).total_seconds() if started_at_dt else None

    # ping à BD com latência
    db_ok = False
    db_latency_ms = None
    try:
        t0 = time.perf_counter()
        db.execute(text("SELECT 1"))
        db_latency_ms = (time.perf_counter() - t0) * 1000.0
        db_ok = True
    except Exception:
        db_ok = False

    # headers úteis
    rid = get_request_id()
    if rid:
        response.headers["X-Request-ID"] = rid
    response.headers["Cache-Control"] = "no-store"

    return HealthDTO(
        ok=True,
        status="ok" if db_ok else "degraded",
        env=settings.APP_ENV,
        now=now,
        uptime_s=uptime_s,
        db_ok=db_ok,
        # novos
        request_id=rid,
        version=getattr(settings, "APP_VERSION", "2.0"),
        service=getattr(settings, "APP_NAME", "genesys-backend"),
        started_at=started_at_dt.isoformat() if started_at_dt else None,
        db_latency_ms=round(db_latency_ms, 1) if db_latency_ms is not None else None,
    )


@router.get("/readyz")
def readyz(request: Request, response: Response, db: SessionDep):
    checks: dict[str, dict] = {}

    # 1) DB + versão de migração
    try:
        db.execute(text("SELECT 1"))
        checks["db"] = {"ok": True}
    except Exception as e:
        checks["db"] = {"ok": False, "error": str(e)[:200]}

    # 2) (Opcional) ping externo – só se a flag estiver ativa
    if getattr(settings, "READINESS_CHECK_EXTERNALS", False):
        try:
            # TODO: faz aqui um ping leve (ex.: HEAD a um endpoint interno/externo)
            checks["external"] = {"ok": True}
        except Exception as e:
            checks["external"] = {"ok": False, "error": str(e)[:200]}

    overall_ok = all(c.get("ok", False) for c in checks.values()) if checks else True
    status = "ok" if overall_ok else "degraded"

    rid = get_request_id()
    if rid:
        response.headers["X-Request-ID"] = rid
    response.headers["Cache-Control"] = "no-store"

    return {
        "ok": overall_ok,
        "status": status,
        "checks": checks,
        "request_id": rid,
        "version": getattr(settings, "APP_VERSION", "2.0"),
    }
