# apps/api_main.py
from __future__ import annotations
from datetime import datetime, timezone
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.core.logging import setup_logging
from app.core.middleware import RequestContextMiddleware

from app.api.v1.system import router as system_router
from app.api.v1.auth import router as auth_router
from app.api.v1.suppliers import router as suppliers_router
from app.api.v1.runs import router as runs_router
from app.api.v1.feeds import router as feeds_router
from app.api.v1.mappers import router as mappers_router

setup_logging()

app = FastAPI(title="Genesys API Backend", version="2.0.0")
app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r".*",   # aceita qualquer origem
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    allow_credentials=True,     # ecoa o Origin em vez de '*'
    max_age=86400,
)

@app.on_event("startup")
async def on_startup():
    app.state.started_at = datetime.now(timezone.utc)
    from app.models import create_db_and_tables
    create_db_and_tables()

# routers
app.include_router(system_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(suppliers_router, prefix="/api/v1")
app.include_router(feeds_router, prefix="/api/v1")
app.include_router(mappers_router, prefix="/api/v1")
app.include_router(runs_router, prefix="/api/v1")