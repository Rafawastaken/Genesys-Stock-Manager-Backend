# app/repositories/supplier_item_repo.py
from __future__ import annotations
from typing import Optional, Tuple, Iterable, Any, Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import select
import hashlib
from app.models.supplier import Supplier
from app.models.supplier_feed import SupplierFeed
from app.models.supplier_item import SupplierItem

def _mk_fp(*parts: str) -> str:
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
        stmt = select(SupplierItem).where(SupplierItem.id_feed == id_feed, SupplierItem.sku == sku)
        item = self.db.scalar(stmt)

        created = False
        changed = False
        old_price: Optional[str] = None
        old_stock: Optional[int] = None

        new_fp = _mk_fp(id_feed, id_product, sku, gtin, partnumber, price, stock)

        if item is None:
            item = SupplierItem(
                id_feed=id_feed,
                id_product=id_product,
                sku=sku,
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


    def list_offers_for_product_ids(
        self,
        product_ids: Iterable[int],
        *,
        only_in_stock: bool = False
    ) -> List[Dict[str, Any]]:
        ids = list(product_ids)
        if not ids:
            return []

        stmt = (
            select(
                SupplierItem.id_product,
                SupplierItem.id_feed.label("id_feed"),
                SupplierItem.sku,
                SupplierItem.price,
                SupplierItem.stock,
                SupplierItem.id_feed_run.label("id_last_seen_run"),  # <- aqui
                SupplierItem.updated_at,
                SupplierFeed.id_supplier,
                Supplier.name.label("supplier_name"),
            )
            .join(SupplierFeed, SupplierFeed.id == SupplierItem.id_feed)
            .join(Supplier, Supplier.id == SupplierFeed.id_supplier)
            .where(SupplierItem.id_product.in_(ids))
        )
        if only_in_stock:
            stmt = stmt.where(SupplierItem.stock > 0)

        rows = self.db.execute(stmt).all()
        out: List[Dict[str, Any]] = []
        for r in rows:
            out.append(
                dict(
                    id_product=r.id_product,
                    id_feed=r.id_feed,
                    sku=r.sku,
                    price=r.price,
                    stock=r.stock,
                    id_last_seen_run=r.id_last_seen_run,
                    updated_at=r.updated_at,
                    id_supplier=r.id_supplier,
                    supplier_name=r.supplier_name,
                )
            )
        return out


