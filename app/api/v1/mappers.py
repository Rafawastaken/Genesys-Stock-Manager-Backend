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
# GET /mappers/feed/{id_feed}
# -------------------------------
@router.get("/feed/{id_feed}")
def get_mapper(id_feed: int, uow: UoW = Depends(get_uow), _=Depends(require_access_token)):
    try:
        return q_get(uow, id_feed=id_feed)
    except ValueError:
        raise HTTPException(status_code=404, detail="Mapper not found")

# -------------------------------
# GET /mappers/supplier/{id_supplier}
# -------------------------------
@router.get("/supplier/{id_supplier}")
def get_mapper_by_supplier(id_supplier: int, uow: UoW = Depends(get_uow), _=Depends(require_access_token)):
    try:
        return q_get_by_supplier(uow, id_supplier=id_supplier)
    except ValueError:
        raise HTTPException(status_code=404, detail="Mapper not found")

# -------------------------------
# POST /mappers/feed/{id_feed}/validate
# -------------------------------
@router.post("/feed/{id_feed}/validate", response_model=MapperValidateOut, dependencies=[Depends(require_access_token)])
def validate_mapper(id_feed: int, payload: MapperValidateIn, uow: UoW = Depends(get_uow)):
    return c_validate(uow, id_feed=id_feed, payload=payload)

# -------------------------------
# GET /mappers/ops
# -------------------------------
@router.get("/ops", dependencies=[Depends(require_access_token)])
def list_ops():
    return supported_ops_for_api()
