# app/api/v1/mappers.py
from __future__ import annotations
import logging
from fastapi import APIRouter, Depends
from app.core.deps import get_uow, require_access_token
from app.infra.uow import UoW
from app.schemas.mappers import FeedMapperOut, FeedMapperUpsert, MapperValidateIn, MapperValidateOut
from app.services.queries.mappers.get_mapper import handle as q_get
from app.services.commands.mappers.put_mapper import handle as c_put
from app.services.commands.mappers.validate_mapper import handle as c_validate
from app.domain.ingest_engine import supported_ops_for_api

router = APIRouter(prefix="/mappers", tags=["mappers"])
log = logging.getLogger("gsm.api.mappers")

@router.get("/feed/{feed_id}", response_model=FeedMapperOut, dependencies=[Depends(require_access_token)])
def get_mapper(feed_id: int, uow: UoW = Depends(get_uow)):
    return q_get(uow, feed_id)

@router.put("/feed/{feed_id}", response_model=FeedMapperOut, dependencies=[Depends(require_access_token)])
def put_mapper(feed_id: int, payload: FeedMapperUpsert, uow: UoW = Depends(get_uow)):
    return c_put(uow, feed_id=feed_id, payload=payload)

@router.post("/feed/{feed_id}/validate", response_model=MapperValidateOut, dependencies=[Depends(require_access_token)])
def validate_mapper(feed_id: int, payload: MapperValidateIn, uow: UoW = Depends(get_uow)):
    return c_validate(uow, feed_id=feed_id, payload=payload)

@router.get("/ops", dependencies=[Depends(require_access_token)])
def list_ops():
    return supported_ops_for_api()
