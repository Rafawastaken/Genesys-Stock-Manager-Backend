from __future__ import annotations

from decimal import Decimal, InvalidOperation

from sqlalchemy import func, select, and_
from sqlalchemy.orm import aliased

from app.domains.procurement.repos import SupplierItemRepository
from app.infra.uow import UoW
from app.models.brand import Brand
from app.models.category import Category
from app.models.product import Product
from app.models.supplier_feed import SupplierFeed
from app.models.supplier_item import SupplierItem
from app.schemas.products import OfferOut, ProductListOut, ProductOut


def _as_decimal(s: str | None) -> Decimal | None:
    if s is None:
        return None
    raw = str(s).strip().replace(" ", "")
    if not raw:
        return None
    try:
        if "," in raw and "." in raw:
            # Se a última vírgula vem depois do último ponto → vírgula é decimal (formato PT)
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
    """
    Choose the lowest-price offer WITH stock.
    If no offer has stock > 0, return None.
    """
    best = None
    best_price = None
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
    sort: str = "recent",  # "recent" | "name" | "cheapest"
    expand_offers: bool = True,  # <— NOVO
) -> ProductListOut:
    db = uow.db
    b = aliased(Brand)
    c = aliased(Category)
    si = aliased(SupplierItem)
    sf = aliased(SupplierFeed)

    base = (
        select(
            Product.id,
            Product.gtin,
            Product.id_ecommerce,
            Product.id_brand,
            Product.id_category,
            Product.partnumber,
            Product.name,
            Product.description,
            Product.image_url,
            Product.weight_str,
            Product.created_at,
            Product.updated_at,
            b.name.label("brand_name"),
            c.name.label("category_name"),
        )
        .select_from(Product)
        .join(b, b.id == Product.id_brand, isouter=True)
        .join(c, c.id == Product.id_category, isouter=True)
    )

    # ... (mesmos filtros que já tens)

    # Ordenação
    if sort == "name":
        base = base.order_by(Product.name.asc().nulls_last())
    elif sort == "cheapest":
        # menor preço entre ofertas com stock>0; NULLS LAST para quem não tem preço com stock
        min_price_with_stock = (
            select(func.min(si.price))
            .select_from(si)
            .join(sf, sf.id == si.id_feed)
            .where(and_(si.id_product == Product.id, si.stock > 0, si.price.isnot(None)))
            .correlate(Product)
            .scalar_subquery()
        )
        base = base.order_by(
            min_price_with_stock.is_(None), min_price_with_stock.asc(), Product.id.asc()
        )
    else:
        base = base.order_by(Product.updated_at.desc().nulls_last(), Product.created_at.desc())

    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0

    page = max(1, page)
    page_size = max(1, min(page_size, 100))
    offset = (page - 1) * page_size

    rows = db.execute(base.limit(page_size).offset(offset)).all()
    if not rows:
        return ProductListOut(items=[], total=int(total), page=page, page_size=page_size)

    ids = [r.id for r in rows]
    items_map: dict[int, ProductOut] = {}
    for r in rows:
        items_map[r.id] = ProductOut(
            id=r.id,
            gtin=r.gtin,
            id_ecommerce=r.id_ecommerce,
            id_brand=r.id_brand,
            brand_name=r.brand_name,
            id_category=r.id_category,
            category_name=r.category_name,
            partnumber=r.partnumber,
            name=r.name,
            description=r.description,
            image_url=r.image_url,
            weight_str=r.weight_str,
            created_at=r.created_at,
            updated_at=r.updated_at,
            offers=[],
            best_offer=None,
        )

    # 2) expand_offers → permite poupar payload quando não precisas das ofertas
    if expand_offers:
        si_repo = SupplierItemRepository(db)
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

    # best_offer continua a usar “stock>0”
    for po in items_map.values():
        po.best_offer = _best_offer(po.offers) if po.offers else None

    return ProductListOut(
        items=[items_map[i] for i in ids],
        total=int(total),
        page=page,
        page_size=page_size,
    )
