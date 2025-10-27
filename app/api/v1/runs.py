# app/api/v1/runs.py

from fastapi import APIRouter, Depends, Query
from app.core.deps import require_access_token
from app.infra.uow import UoW
from app.core.deps import get_uow
from app.services.commands.runs import ingest_supplier as c_ingest

router = APIRouter(prefix="/runs", tags=["runs"])

@router.post("/supplier/{id_supplier}/ingest")
async def ingest_supplier(id_supplier: int,
                          limit: int | None = Query(default=None, ge=1, le=1_000_000),
                          uow:UoW = Depends(get_uow),
                          _=Depends(require_access_token)):
    return await c_ingest.handle(uow, id_supplier=id_supplier, limit=limit)
