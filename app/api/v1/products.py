from __future__ import annotations

import logging
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, Path

from app.core.deps import get_uow, require_access_token
from app.schemas.products import ProductDetailOut, ProductListOut
from app.domains.catalog.usecases.products.list_products import execute as uc_q_list_products
from app.domains.catalog.usecases.products.get_product_detail import execute as uc_q_product_detail
from app.domains.catalog.usecases.products.get_product_by_gtin import (
    execute as uc_q_product_detail_by_gtin,
)
from app.infra.uow import UoW

router = APIRouter(prefix="/products", tags=["products"])
log = logging.getLogger("gsm.api.products")
UowDep = Annotated[UoW, Depends(get_uow)]


@router.get(
    "",
    dependencies=[Depends(require_access_token)],
    summary="Get Product List",
    response_model=ProductListOut,
)
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


@router.get(
    "/{id_product}",
    dependencies=[Depends(require_access_token)],
    response_model=ProductDetailOut,
    summary="Get Product Details by ID",
)
def get_product_detail(
    id_product: int,
    expand_meta: bool = Query(True),
    expand_offers: bool = Query(True),
    expand_events: bool = Query(True),
    events_days: int | None = Query(90, ge=1, le=3650),
    events_limit: int | None = Query(2000, ge=1, le=100000),
    aggregate_daily: bool = Query(True),
    uow: UoW = Depends(get_uow),
):
    return uc_q_product_detail(
        uow,
        id_product=id_product,
        expand_meta=expand_meta,
        expand_offers=expand_offers,
        expand_events=expand_events,
        events_days=events_days,
        events_limit=events_limit,
        aggregate_daily=aggregate_daily,
    )


@router.get(
    "/gtin/{gtin}",
    response_model=ProductDetailOut,
    dependencies=[Depends(require_access_token)],
    summary="Get Product Detail by GTIN",
)
def get_product_detail_by_gtin(
    gtin: Annotated[str, Path(min_length=8, max_length=18, pattern=r"^\d{8,18}$")],
    expand_meta: bool = Query(True),
    expand_offers: bool = Query(True),
    expand_events: bool = Query(True),
    events_days: int | None = Query(90, ge=1, le=3650),
    events_limit: int | None = Query(2000, ge=1, le=100000),
    aggregate_daily: bool = Query(True),
    uow: UoW = Depends(get_uow),
) -> ProductDetailOut:
    return uc_q_product_detail_by_gtin(
        uow,
        gtin=gtin.strip(),
        expand_meta=expand_meta,
        expand_offers=expand_offers,
        expand_events=expand_events,
        events_days=events_days,
        events_limit=events_limit,
        aggregate_daily=aggregate_daily,
    )
