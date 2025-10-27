from __future__ import annotations
import logging
from fastapi import APIRouter, Depends, Query
from app.core.deps import get_uow, require_access_token
from app.infra.uow import UoW
from app.services.queries.products import list_products as q_list

router = APIRouter(prefix="/products", tags=["products"])
log = logging.getLogger("gsm.api.products")

@router.get("")
def get_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: str | None = None,
    gtin: str | None = None,
    partnumber: str | None = None,
    id_brand: int | None = None,
    brand: str | None = None,
    id_category: int | None = None,
    category: str | None = None,
    has_stock: bool | None = None,
    id_supplier: int | None = None,
    sort: str = Query("recent", regex="^(recent|name)$"),
    uow: UoW = Depends(get_uow),
    _=Depends(require_access_token),
):
    return q_list.handle(
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
    )
