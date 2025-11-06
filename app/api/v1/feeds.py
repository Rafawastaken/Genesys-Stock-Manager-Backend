# app/api/v1/feeds.py
from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.deps import get_uow, require_access_token
from app.domains.procurement.usecases.feeds.delete_supplier_feed import execute as uc_delete
from app.domains.procurement.usecases.feeds.get_by_supplier import (
    _to_out,
    execute as uc_get_feed_by_supplier,
)
from app.domains.procurement.usecases.feeds.test_feed import execute as uc_test
from app.domains.procurement.usecases.feeds.upsert_supplier_feed import execute as uc_upsert
from app.infra.uow import UoW
from app.schemas.feeds import (
    FeedTestRequest,
    FeedTestResponse,
    SupplierFeedCreate,
    SupplierFeedOut,
    SupplierFeedUpdate,
)

router = APIRouter(prefix="/feeds", tags=["feeds"])
UowDep = Annotated[UoW, Depends(get_uow)]
log = logging.getLogger("gsm.api.feeds")


@router.get("/supplier/{id_supplier}", dependencies=[Depends(require_access_token)])
def get_supplier_feed(id_supplier: int, uow: UowDep):
    e = uc_get_feed_by_supplier(uow, id_supplier=id_supplier)
    return _to_out(e)


@router.put(
    "/supplier/{id_supplier}",
    response_model=SupplierFeedOut,
    dependencies=[Depends(require_access_token)],
)
def upsert_supplier_feed(
    id_supplier: int, payload: SupplierFeedCreate | SupplierFeedUpdate, uow: UowDep
):
    return uc_upsert(uow, id_supplier=id_supplier, data=payload)


@router.delete(
    "/supplier/{id_supplier}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_access_token)],
)
def delete_supplier_feed(id_supplier: int, uow: UowDep):
    uc_delete(uow, id_supplier=id_supplier)
    return


@router.post("/test", response_model=FeedTestResponse, dependencies=[Depends(require_access_token)])
async def test_feed(payload: FeedTestRequest):
    return await uc_test(payload)
