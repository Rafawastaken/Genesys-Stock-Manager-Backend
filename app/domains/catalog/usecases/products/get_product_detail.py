# app/domains/catalog/usecases/products/get_product_detail.py

from __future__ import annotations
from decimal import Decimal, InvalidOperation
from datetime import datetime

from app.core.errors import NotFound
from app.infra.uow import UoW
from app.domains.catalog.repos import ProductsReadRepository, ProductMetaReadRepository
from app.domains.procurement.repos import SupplierItemReadRepository, ProductEventReadRepository
from app.schemas.products import (
    ProductOut,
    ProductMetaOut,
    OfferOut,
    ProductEventOut,
    ProductDetailOut,
    ProductStatsOut,
    SeriesPointOut,
)


def _as_decimal(s: str | None) -> Decimal | None:
    if s is None:
        return None
    raw = str(s).strip().replace(" ", "")
    if not raw:
        return None
    try:
        if "," in raw and "." in raw:
            if raw.rfind(",") > raw.rfind("."):
                raw = raw.replace(".", "").replace(",", ".")
            else:
                raw = raw.replace(",", "")
        else:
            raw = raw.replace(",", ".")
        return Decimal(raw)
    except (InvalidOperation, ValueError):
        return None


def _best_offer(offers: list[OfferOut]) -> OfferOut | None:
    best, best_price = None, None
    for o in offers:
        if (o.stock or 0) <= 0:
            continue
        p = _as_decimal(o.price)
        if p is None:
            continue
        if best is None or p < best_price:
            best, best_price = o, p
    return best


def _aggregate_daily(events: list[ProductEventOut]) -> list[SeriesPointOut]:
    # Consolida por dia (último valor do dia)
    bucket: dict[str, SeriesPointOut] = {}
    for e in events:
        day = e.ts.strftime("%Y-%m-%d")
        # current = bucket.get(day)
        point = SeriesPointOut(
            date=datetime.fromisoformat(day + "T00:00:00"),
            price=e.price,
            stock=e.stock,
        )
        # mantemos o último do dia (ordem já asc)
        bucket[day] = point
    # ordenar por data
    return [bucket[k] for k in sorted(bucket.keys())]


def execute(
    uow: UoW,
    *,
    id_product: int,
    expand_meta: bool = True,
    expand_offers: bool = True,
    expand_events: bool = True,
    events_days: int | None = 90,
    events_limit: int | None = 2000,
    aggregate_daily: bool = True,
) -> ProductDetailOut:
    db = uow.db

    # 1) base product + nomes agregados
    p_repo = ProductsReadRepository(db)
    row = p_repo.get_product_with_names(id_product)
    if not row:
        raise NotFound("Product not found")

    p = ProductOut(
        id=row.id,
        gtin=row.gtin,
        id_ecommerce=row.id_ecommerce,
        id_brand=row.id_brand,
        brand_name=row.brand_name,
        id_category=row.id_category,
        category_name=row.category_name,
        partnumber=row.partnumber,
        name=row.name,
        description=row.description,
        image_url=row.image_url,
        weight_str=row.weight_str,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )

    # 2) meta
    meta_list: list[ProductMetaOut] = []
    if expand_meta:
        m_repo = ProductMetaReadRepository(db)
        ms = m_repo.list_for_product(p.id)
        meta_list = [ProductMetaOut(name=m.name, value=m.value or "") for m in ms]

    # 3) offers
    offers: list[OfferOut] = []
    offers_in_stock = 0
    suppliers_set: set[int] = set()
    if expand_offers:
        si_repo = SupplierItemReadRepository(db)
        offers_raw = si_repo.list_offers_for_product(p.id, only_in_stock=False)
        for o in offers_raw:
            offer = OfferOut(
                id_supplier=o["id_supplier"],
                supplier_name=o.get("supplier_name"),
                supplier_image=o.get("supplier_image"),
                id_feed=o["id_feed"],
                sku=o["sku"],
                price=o["price"],
                stock=o["stock"],
                id_last_seen_run=o.get("id_last_seen_run"),
                updated_at=o.get("updated_at"),
            )
            offers.append(offer)
            if (offer.stock or 0) > 0:
                offers_in_stock += 1
            if o.get("id_supplier"):
                suppliers_set.add(int(o["id_supplier"]))

    best = _best_offer(offers) if offers else None

    # 4) events + séries
    events_out: list[ProductEventOut] | None = None
    series_daily: list[SeriesPointOut] | None = None
    first_seen = None
    last_seen = None
    last_change_at = None

    if expand_events:
        ev_repo = ProductEventReadRepository(db)
        evs = ev_repo.list_events_for_product(p.id, days=events_days, limit=events_limit)
        if evs:
            events_out = [
                ProductEventOut(
                    created_at=e["created_at"],
                    reason=e["reason"],
                    price=e.get("price"),
                    stock=e.get("stock"),
                    id_supplier=e.get("id_supplier"),
                    supplier_name=e.get("supplier_name"),
                    id_feed_run=e.get("id_feed_run"),
                )
                for e in evs
            ]
            first_seen = evs[0]["created_at"]
            last_seen = evs[-1]["created_at"]
            # último evento com reason != 'init' (se existir)
            for e in reversed(evs):
                if (e.get("reason") or "").lower() != "init":
                    last_change_at = e["created_at"]
                    break
            if aggregate_daily:
                series_daily = _aggregate_daily(events_out)

    stats = ProductStatsOut(
        first_seen=first_seen or p.created_at,
        last_seen=last_seen or p.updated_at or p.created_at,
        suppliers_count=len(suppliers_set),
        offers_in_stock=offers_in_stock,
        last_change_at=last_change_at,
    )

    return ProductDetailOut(
        product=p,
        meta=meta_list,
        offers=offers,
        best_offer=best,
        stats=stats,
        events=events_out,
        series_daily=series_daily,
    )
