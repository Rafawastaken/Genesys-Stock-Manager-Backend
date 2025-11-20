from __future__ import annotations

import logging
from fastapi import APIRouter, Depends, Query, Path
from typing import Annotated, Literal

from app.core.deps import get_uow, require_access_token
from app.domains.catalog.usecases.products.get_product_by_gtin import (
    execute as uc_q_product_detail_by_gtin,
)
from app.domains.catalog.usecases.products.get_product_detail import (
    execute as uc_q_product_detail,
)
from app.domains.catalog.usecases.products.list_products import (
    execute as uc_q_list_products,
)
from app.domains.catalog.usecases.products.update_margin import (
    execute as uc_update_product_margin,
)
from app.infra.uow import UoW
from app.schemas.products import ProductDetailOut, ProductListOut, ProductMarginUpdate

router = APIRouter(
    prefix="/products", tags=["products"], dependencies=[Depends(require_access_token)]
)
log = logging.getLogger("gsm.api.products")

# Aqui está o Depends já embutido
UowDep = Annotated[UoW, Depends(get_uow)]


@router.get(
    "",
    summary="Get Product List",
    response_model=ProductListOut,
)
def list_products(
    uow: UowDep,
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
    response_model=ProductDetailOut,
    summary="Get Product Details by ID",
)
def get_product_detail(
    uow: UowDep,
    id_product: int,
    expand_meta: bool = Query(True),
    expand_offers: bool = Query(True),
    expand_events: bool = Query(True),
    events_days: int | None = Query(90, ge=1, le=3650),
    events_limit: int | None = Query(2000, ge=1, le=100000),
    aggregate_daily: bool = Query(True),
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
    summary="Get Product Detail by GTIN",
)
def get_product_detail_by_gtin(
    uow: UowDep,
    gtin: Annotated[str, Path(min_length=8, max_length=18, pattern=r"^\d{8,18}$")],
    expand_meta: bool = Query(True),
    expand_offers: bool = Query(True),
    expand_events: bool = Query(True),
    events_days: int | None = Query(90, ge=1, le=3650),
    events_limit: int | None = Query(2000, ge=1, le=100000),
    aggregate_daily: bool = Query(True),
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


@router.patch(
    "/{id_product}/margin",
    response_model=ProductDetailOut,
)
def update_product_margin(
    id_product: int = Path(..., ge=1),
    payload: ProductMarginUpdate = ...,
    uow: UowDep = None,
    expand_meta: bool = Query(True),
    expand_offers: bool = Query(True),
    expand_events: bool = Query(True),
    events_days: int | None = Query(90, ge=1, le=3650),
    events_limit: int | None = Query(2000, ge=1, le=100000),
    aggregate_daily: bool = Query(True),
) -> ProductDetailOut:
    """
    Atualiza a margem de um produto e devolve o detalhe atualizado.

    Mantemos as mesmas flags de expansão do GET /products/{id_product}
    para poderes reutilizar este endpoint no frontend sem teres de re-fetchar
    o detalhe numa segunda chamada.
    """
    return uc_update_product_margin(
        uow,
        id_product=id_product,
        margin=payload.margin,
        expand_meta=expand_meta,
        expand_offers=expand_offers,
        expand_events=expand_events,
        events_days=events_days,
        events_limit=events_limit,
        aggregate_daily=aggregate_daily,
    )
