# app/api/v1/mappers.py
from __future__ import annotations
import logging
from fastapi import APIRouter, Depends, HTTPException
from app.core.deps import get_uow, require_access_token
from app.infra.uow import UoW
from app.schemas.mappers import MapperValidateIn, MapperValidateOut
from app.services.queries.mappers.get_mapper import handle as q_get
from app.services.queries.mappers.get_by_supplier import handle as q_get_by_supplier
from app.services.commands.mappers.validate_mapper import handle as c_validate
from app.domain.ingest_engine import supported_ops_for_api

router = APIRouter(prefix="/mappers", tags=["mappers"])
log = logging.getLogger("gsm.api.mappers")

# -------------------------------
# GET /mappers/feed/{feed_id}
# -------------------------------
@router.get("/feed/{feed_id}")
def get_mapper(feed_id: int, uow: UoW = Depends(get_uow), _=Depends(require_access_token)):
    try:
        return q_get(uow, feed_id=feed_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Mapper not found")

# -------------------------------
# GET /mappers/supplier/{supplier_id}
# -------------------------------
@router.get("/supplier/{supplier_id}")
def get_mapper_by_supplier(supplier_id: int, uow: UoW = Depends(get_uow), _=Depends(require_access_token)):
    try:
        return q_get_by_supplier(uow, supplier_id=supplier_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Mapper not found")

# -------------------------------
# POST /mappers/feed/{feed_id}/validate
# -------------------------------
@router.post("/feed/{feed_id}/validate", response_model=MapperValidateOut, dependencies=[Depends(require_access_token)])
def validate_mapper(feed_id: int, payload: MapperValidateIn, uow: UoW = Depends(get_uow)):
    return c_validate(uow, feed_id=feed_id, payload=payload)

# -------------------------------
# GET /mappers/ops
# -------------------------------
@router.get("/ops", dependencies=[Depends(require_access_token)])
def list_ops():
    return supported_ops_for_api()
