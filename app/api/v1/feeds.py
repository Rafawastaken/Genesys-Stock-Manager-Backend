# app/api/v1/feeds.py
from __future__ import annotations
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.core.deps import get_uow, require_access_token
from app.infra.uow import UoW
from app.schemas.feeds import (
    SupplierFeedCreate, SupplierFeedUpdate, SupplierFeedOut,
    FeedTestRequest, FeedTestResponse
)
from app.services.queries.feeds.get_by_supplier import handle as q_get_by_supplier
from app.services.commands.feeds.upsert_supplier_feed import handle as c_upsert
from app.services.commands.feeds.delete_supplier_feed import handle as c_delete
from app.services.commands.feeds.test_feed import handle as c_test

router = APIRouter(prefix="/feeds", tags=["feeds"])
log = logging.getLogger("gsm.api.feeds")

@router.get("/supplier/{id_supplier}")
def get_supplier_feed(id_supplier: int, uow: UoW = Depends(get_uow), _=Depends(require_access_token)):
    try:
        return q_get_by_supplier(uow, id_supplier=id_supplier)
    except ValueError:
        raise HTTPException(status_code=404, detail="Feed not found")

@router.put("/supplier/{id_supplier}", response_model=SupplierFeedOut, dependencies=[Depends(require_access_token)])
def upsert_supplier_feed(
    id_supplier: int,
    payload: SupplierFeedCreate | SupplierFeedUpdate,
    uow: UoW = Depends(get_uow),
):
    return c_upsert(uow, id_supplier=id_supplier, data=payload)

@router.delete("/supplier/{id_supplier}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_access_token)])
def delete_supplier_feed(id_supplier: int, uow: UoW = Depends(get_uow)):
    c_delete(uow, id_supplier=id_supplier)
    return

@router.post("/test", response_model=FeedTestResponse, dependencies=[Depends(require_access_token)])
async def test_feed(payload: FeedTestRequest):
    # não precisa de UoW; é um fetch externo / preview
    return await c_test(payload)
