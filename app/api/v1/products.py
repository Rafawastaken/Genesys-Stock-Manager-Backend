from __future__ import annotations

import logging
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query

from app.core.deps import get_uow, require_access_token
from app.domains.catalog.usecases.products.list_products import execute as uc_q_list_products
from app.infra.uow import UoW

router = APIRouter(prefix="/products", tags=["products"])
log = logging.getLogger("gsm.api.products")
UowDep = Annotated[UoW, Depends(get_uow)]


@router.get("", dependencies=[Depends(require_access_token)])
def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: str | None = Query(None),
    gtin: str | None = Query(None),
    partnumber: str | None = Query(None),
    id_brand: int | None = Query(None),
    brand: str | None = Query(None),
    id_category: int | None = Query(None),
    category: str | None = Query(None),
    has_stock: bool | None = Query(None),
    id_supplier: int | None = Query(None),
    sort: Literal["recent", "name", "cheapest"] = Query("recent"),
    expand_offers: bool = Query(True),
    uow: UoW = Depends(get_uow),
):
    return uc_q_list_products(
        uow,
        page=page,
        page_size=page_size,
        q=q,
        gtin=gtin,
        partnumber=partnumber,
        id_brand=id_brand,
        brand=brand,
        id_category=id_category,
        category=category,
        has_stock=has_stock,
        id_supplier=id_supplier,
        sort=sort,
        expand_offers=expand_offers,
    )
