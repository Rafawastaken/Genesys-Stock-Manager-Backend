# app/domains/catalog/usecases/products/list_products.py
from __future__ import annotations
from decimal import Decimal, InvalidOperation
from collections.abc import Iterable

from app.infra.uow import UoW
from app.domains.catalog.repos import ProductsReadRepository
from app.domains.procurement.repos import SupplierItemReadRepository
from app.schemas.products import OfferOut, ProductListOut, ProductOut


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


def _best_offer(offers: Iterable[OfferOut]) -> OfferOut | None:
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


def execute(
    uow: UoW,
    *,
    page: int = 1,
    page_size: int = 20,
    q: str | None = None,
    gtin: str | None = None,
    partnumber: str | None = None,
    id_brand: int | None = None,
    brand: str | None = None,
    id_category: int | None = None,
    category: str | None = None,
    has_stock: bool | None = None,
    id_supplier: int | None = None,
    sort: str = "recent",  # "recent" | "name" | "cheapest" (repo trata disto)
    expand_offers: bool = True,
) -> ProductListOut:
    db = uow.db

    # 1) Lista produtos via READ repo (sem SQL aqui)
    prod_repo = ProductsReadRepository(db)
    rows, total = prod_repo.list_products(
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

    if not rows:
        return ProductListOut(items=[], total=int(total), page=page, page_size=page_size)

    # 2) Mapear rows → ProductOut (campos agregados brand_name/category_name já vêm do repo)
    items_map: dict[int, ProductOut] = {}
    ids: list[int] = []
    for r in rows:
        ids.append(r.id)
        items_map[r.id] = ProductOut(
            id=r.id,
            gtin=r.gtin,
            id_ecommerce=r.id_ecommerce,
            id_brand=r.id_brand,
            brand_name=getattr(r, "brand_name", None),
            id_category=r.id_category,
            category_name=getattr(r, "category_name", None),
            partnumber=r.partnumber,
            name=r.name,
            description=r.description,
            image_url=r.image_url,
            weight_str=r.weight_str,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )

    # 3) Opcionalmente expandir ofertas via Procurement READ repo
    if expand_offers:
        si_repo = SupplierItemReadRepository(db)
        offers_raw = si_repo.list_offers_for_product_ids(ids, only_in_stock=False)
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
            items_map[o["id_product"]].offers.append(offer)

    # 4) best_offer (stock > 0)
    for po in items_map.values():
        po.best_offer = _best_offer(po.offers) if po.offers else None

    return ProductListOut(
        items=[items_map[i] for i in ids],
        total=int(total),
        page=page,
        page_size=page_size,
    )
