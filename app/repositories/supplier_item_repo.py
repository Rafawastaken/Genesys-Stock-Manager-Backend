from __future__ import annotations
from typing import Optional, Tuple, Iterable, Any, Dict, List, Sequence
from sqlalchemy.orm import Session
from sqlalchemy import select
import hashlib

from app.models.supplier import Supplier
from app.models.supplier_feed import SupplierFeed
from app.models.supplier_item import SupplierItem
from app.core.errors import InvalidArgument

def _mk_fp(*parts: Any) -> str:
    raw = "|".join("" if p is None else str(p) for p in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

class SupplierItemRepository:
    def __init__(self, db: Session):
        self.db = db

    def upsert(
        self,
        *,
        id_feed: int,
        id_product: int,
        sku: str,
        price: str,
        stock: int,
        gtin: Optional[str],
        partnumber: Optional[str],
        id_feed_run: int,
    ) -> Tuple[SupplierItem, bool, bool, Optional[str], Optional[int]]:
        sku_norm = (sku or "").strip()
        if not sku_norm:
            raise InvalidArgument("SKU is empty")

        stmt = select(SupplierItem).where(SupplierItem.id_feed == id_feed, SupplierItem.sku == sku_norm)
        item = self.db.scalar(stmt)

        created = False
        changed = False
        old_price: Optional[str] = None
        old_stock: Optional[int] = None

        new_fp = _mk_fp(id_feed, id_product, sku_norm, gtin, partnumber, price, stock)

        if item is None:
            item = SupplierItem(
                id_feed=id_feed,
                id_product=id_product,
                sku=sku_norm,
                gtin=gtin,
                partnumber=partnumber,
                price=price,
                stock=stock,
                fingerprint=new_fp,
                id_feed_run=id_feed_run,
            )
            self.db.add(item)
            created = True
        else:
            old_price = item.price
            old_stock = item.stock
            changed = (
                (old_price != price)
                or (old_stock != stock)
                or (item.id_product != id_product)
                or (item.gtin != gtin)
                or (item.partnumber != partnumber)
            )

            item.id_product = id_product
            item.gtin = gtin
            item.partnumber = partnumber
            item.price = price
            item.stock = stock
            item.id_feed_run = id_feed_run
            item.fingerprint = new_fp

        self.db.flush()
        return item, created, changed, old_price, old_stock

    def list_offers_for_product_ids(self, product_ids: Sequence[int], only_in_stock: bool = False) -> List[Dict[str, Any]]:
        si = SupplierItem
        sf = SupplierFeed
        s  = Supplier

        q = (
            select(
                si.id_product.label("id_product"),
                si.id_feed.label("id_feed"),
                sf.id_supplier.label("id_supplier"),
                s.name.label("supplier_name"),
                s.logo_image.label("supplier_image"),
                si.sku.label("sku"),
                si.price.label("price"),
                si.stock.label("stock"),
                si.id_feed_run.label("id_last_seen_run"),
                si.updated_at.label("updated_at"),
            )
            .join(sf, sf.id == si.id_feed)
            .join(s, s.id == sf.id_supplier)
            .where(si.id_product.in_(list(product_ids)))
        )

        if only_in_stock:
            q = q.where(si.stock > 0)

        return [dict(r._mapping) for r in self.db.execute(q).all()]
