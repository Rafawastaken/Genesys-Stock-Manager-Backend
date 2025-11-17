from __future__ import annotations
from dataclasses import dataclass

from app.infra.uow import UoW
from app.repositories.catalog.read.product_active_offer_read_repo import (
    ProductActiveOfferReadRepository,
)
from app.repositories.catalog.read.product_meta_read_repo import ProductMetaReadRepository
from app.repositories.catalog.read.products_read_repo import ProductsReadRepository
from app.repositories.procurement.read.product_event_read_repo import (
    ProductEventReadRepository,
)
from app.repositories.procurement.read.supplier_item_read_repo import (
    SupplierItemReadRepository,
)
from app.schemas.products import (
    ProductOut,
    ProductMetaOut,
    OfferOut,
    ProductEventOut,
    ProductDetailOut,
    ProductStatsOut,
    SeriesPointOut,
)
from app.domains.catalog.services.mappers import (
    map_product_row_to_out,
    map_offer_row_to_out,
)
from .series import aggregate_daily_points


@dataclass(frozen=True)
class DetailOptions:
    expand_meta: bool = True
    expand_offers: bool = True
    expand_events: bool = True
    events_days: int | None = 90
    events_limit: int | None = 2000
    aggregate_daily: bool = True


def get_product_detail(uow: UoW, *, id_product: int, opts: DetailOptions) -> ProductDetailOut:
    db = uow.db

    # 1) produto + nomes agregados
    p_repo = ProductsReadRepository(db)
    row = p_repo.get_product_with_names(id_product)
    if not row:
        from app.core.errors import NotFound

        raise NotFound("Product not found")

    # usar mapper base (sem offers)
    p: ProductOut = map_product_row_to_out(row)

    # 2) meta
    meta_list: list[ProductMetaOut] = []
    if opts.expand_meta:
        m_repo = ProductMetaReadRepository(db)
        ms = m_repo.list_for_product(p.id)
        meta_list = [
            ProductMetaOut(name=m.name, value=m.value or "", created_at=m.created_at) for m in ms
        ]

    # 3) ofertas
    offers: list[OfferOut] = []
    offers_in_stock = 0
    suppliers_set: set[int] = set()
    if opts.expand_offers:
        si_repo = SupplierItemReadRepository(db)
        offers_raw = si_repo.list_offers_for_product(p.id, only_in_stock=False)
        for o in offers_raw:
            offer: OfferOut = map_offer_row_to_out(o)
            offers.append(offer)
            if (offer.stock or 0) > 0:
                offers_in_stock += 1
            if o.get("id_supplier"):
                suppliers_set.add(int(o["id_supplier"]))

    # 3.1) best_offer = oferta do supplier ativo (ProductActiveOffer)
    best = None
    if offers:
        pao_repo = ProductActiveOfferReadRepository(db)
        pao = pao_repo.get_by_product(p.id)
        if pao and pao.id_supplier is not None:
            for o in offers:
                if o.id_supplier == pao.id_supplier:
                    best = o
                    break

    # 4) eventos + séries
    events_out: list[ProductEventOut] | None = None
    series_daily: list[SeriesPointOut] | None = None
    first_seen = None
    last_seen = None
    last_change_at = None

    if opts.expand_events:
        ev_repo = ProductEventReadRepository(db)
        evs = ev_repo.list_events_for_product(p.id, days=opts.events_days, limit=opts.events_limit)
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
            for e in reversed(evs):
                if (e.get("reason") or "").lower() != "init":
                    last_change_at = e["created_at"]
                    break
            if opts.aggregate_daily:
                series_daily = aggregate_daily_points(events_out)

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
