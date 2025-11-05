# app/api/v1/runs.py

from fastapi import APIRouter, Depends, Query
from app.core.deps import require_access_token
from app.infra.uow import UoW
from app.core.deps import get_uow
from app.domains.procurement.usecases.runs.ingest_supplier import execute as uc_ingest

router = APIRouter(prefix="/runs", tags=["runs"])

@router.post("/supplier/{id_supplier}/ingest")
async def ingest_supplier(id_supplier: int,
                          limit: int | None = Query(default=None, ge=1, le=1_000_000),
                          uow:UoW = Depends(get_uow),
                          _=Depends(require_access_token)):
    return await uc_ingest(uow, id_supplier=id_supplier, limit=limit)
