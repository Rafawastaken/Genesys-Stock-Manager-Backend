from __future__ import annotations
import re

from app.core.errors import NotFound
from app.infra.uow import UoW
from app.domains.catalog.repos import ProductsReadRepository
from app.domains.catalog.usecases.products.get_product_detail import execute as q_product_detail
from app.schemas.products import ProductDetailOut


def _normalize_gtin(gtin: str) -> str:
    # remove espaços, hífens, etc. — fica só dígito
    return re.sub(r"\D", "", (gtin or "").strip())


def execute(
    uow: UoW,
    *,
    gtin: str,
    expand_meta: bool = True,
    expand_offers: bool = True,
    expand_events: bool = True,
    events_days: int | None = 90,
    events_limit: int | None = 2000,
    aggregate_daily: bool = True,
) -> ProductDetailOut:
    norm = _normalize_gtin(gtin)
    if not norm:
        raise NotFound("GTIN inválido.")

    p_repo = ProductsReadRepository(uow.db)
    id_product = p_repo.get_id_by_gtin(norm)
    if not id_product:
        # tenta sem normalização se guardaste GTIN com formatação
        id_product = p_repo.get_id_by_gtin(gtin)

    if not id_product:
        raise NotFound(f"Product with GTIN {gtin} not found.")

    return q_product_detail(
        uow,
        id_product=id_product,
        expand_meta=expand_meta,
        expand_offers=expand_offers,
        expand_events=expand_events,
        events_days=events_days,
        events_limit=events_limit,
        aggregate_daily=aggregate_daily,
    )
