from __future__ import annotations
from typing import Optional, Dict, List
from decimal import Decimal, InvalidOperation

from sqlalchemy import select, func, exists
from sqlalchemy.orm import aliased

from app.infra.uow import UoW
from app.models.product import Product
from app.models.brand import Brand
from app.models.category import Category
from app.models.supplier_item import SupplierItem
from app.models.supplier_feed import SupplierFeed
from app.schemas.products import ProductListOut, ProductOut, OfferOut
from app.domains.procurement.repos import SupplierItemRepository

def _as_decimal(s: str) -> Optional[Decimal]:
    if s is None:
        return None
    try:
        return Decimal(str(s).strip().replace(",", "."))
    except (InvalidOperation, ValueError):
        return None

def _best_offer(offers: List[OfferOut]) -> Optional[OfferOut]:
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
    q: Optional[str] = None,
    gtin: Optional[str] = None,
    partnumber: Optional[str] = None,
    id_brand: Optional[int] = None,
    brand: Optional[str] = None,
    id_category: Optional[int] = None,
    category: Optional[str] = None,
    has_stock: Optional[bool] = None,
    id_supplier: Optional[int] = None,
    sort: str = "recent",
) -> ProductListOut:
    db = uow.db
    b = aliased(Brand)
    c = aliased(Category)

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

    if q:
        like = f"%{q.strip()}%"
        base = base.where(
            Product.name.ilike(like)
            | Product.partnumber.ilike(like)
            | Product.gtin.ilike(like)
        )
    if gtin:
        base = base.where(Product.gtin == gtin)
    if partnumber:
        base = base.where(Product.partnumber == partnumber)
    if id_brand:
        base = base.where(Product.id_brand == id_brand)
    if brand:
        base = base.where(b.name.ilike(f"%{brand.strip()}%"))
    if id_category:
        base = base.where(Product.id_category == id_category)
    if category:
        base = base.where(c.name.ilike(f"%{category.strip()}%"))

    if has_stock is not None or id_supplier is not None:
        si = aliased(SupplierItem)
        sf = aliased(SupplierFeed)
        exists_q = (
            select(1)
            .select_from(si)
            .join(sf, sf.id == si.id_feed)
            .where(si.id_product == Product.id)
        )
        if has_stock is True:
            exists_q = exists_q.where(si.stock > 0)
        if id_supplier is not None:
            exists_q = exists_q.where(sf.id_supplier == id_supplier)
        base = base.where(exists(exists_q))

    if sort == "name":
        base = base.order_by(Product.name.asc().nulls_last())
    else:
        base = base.order_by(
            Product.updated_at.desc().nulls_last(),
            Product.created_at.desc()
        )

    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0

    page = max(1, page)
    page_size = max(1, min(page_size, 100))
    offset = (page - 1) * page_size

    rows = db.execute(base.limit(page_size).offset(offset)).all()
    if not rows:
        return ProductListOut(items=[], total=int(total), page=page, page_size=page_size)

    ids = [r.id for r in rows]
    items_map: Dict[int, ProductOut] = {}
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

    for po in items_map.values():
        po.best_offer = _best_offer(po.offers) if po.offers else None

    return ProductListOut(
        items=[items_map[i] for i in ids],
        total=int(total),
        page=page,
        page_size=page_size,
    )
