# app/api/v1/feeds.py
from __future__ import annotations
import logging

from fastapi import APIRouter, Depends, status

from app.core.deps import get_uow, require_access_token
from app.infra.uow import UoW
from app.schemas.feeds import (
    SupplierFeedCreate, SupplierFeedUpdate, SupplierFeedOut,
    FeedTestRequest, FeedTestResponse
)
from app.domains.procurement.usecases.feeds.upsert_supplier_feed import execute as uc_upsert
from app.domains.procurement.usecases.feeds.delete_supplier_feed import execute as uc_delete
from app.domains.procurement.usecases.feeds.test_feed import execute as uc_test
from app.domains.procurement.usecases.feeds.get_by_supplier import (
    execute as uc_get_feed_by_supplier,
    _to_out,
)

router = APIRouter(prefix="/feeds", tags=["feeds"])
log = logging.getLogger("gsm.api.feeds")


@router.get("/supplier/{id_supplier}", response_model=SupplierFeedOut)
def get_supplier_feed(
    id_supplier: int,
    uow: UoW = Depends(get_uow),
    _=Depends(require_access_token),
):
    e = uc_get_feed_by_supplier(uow, id_supplier=id_supplier)  # levanta NotFound se não existir
    return _to_out(e)

@router.put("/supplier/{id_supplier}", response_model=SupplierFeedOut, dependencies=[Depends(require_access_token)])
def upsert_supplier_feed(
    id_supplier: int,
    payload: SupplierFeedCreate | SupplierFeedUpdate,
    uow: UoW = Depends(get_uow),
):
    return uc_upsert(uow, id_supplier=id_supplier, data=payload)


@router.delete("/supplier/{id_supplier}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_access_token)])
def delete_supplier_feed(id_supplier: int, uow: UoW = Depends(get_uow)):
    uc_delete(uow, id_supplier=id_supplier)
    return


@router.post("/test", response_model=FeedTestResponse, dependencies=[Depends(require_access_token)])
async def test_feed(payload: FeedTestRequest):
    return await uc_test(payload)
