# app/repositories/product_event_repo.py
# Repository for managing ProductSupplierEvent entities.

from typing import Optional, List
from sqlalchemy import select, or_
from sqlalchemy.orm import Session
from .base import Repository
from app.models.product_supplier_event import ProductSupplierEvent
from app.models.product import Product
from app.models.supplier_item import SupplierItem

class ProductEventRepository(Repository[ProductSupplierEvent]):
    def __init__(self, db: Session): super().__init__(db, ProductSupplierEvent)

    def last_for(self, product_id: int, supplier_id: int) -> Optional[ProductSupplierEvent]:
        return self.db.scalar(
            select(ProductSupplierEvent)
            .where(ProductSupplierEvent.id_product==product_id,
                   ProductSupplierEvent.id_supplier==supplier_id)
            .order_by(ProductSupplierEvent.created_at.desc(), ProductSupplierEvent.id.desc())
        )

    def add_change_if_needed(self, *, product_id: int, supplier_id: int,
                             price: str, stock: int, supplier_partnumber: str|None,
                             feed_run_id: int|None) -> Optional[ProductSupplierEvent]:
        last = self.last_for(product_id, supplier_id)
        if last and last.price == price and last.stock == stock:
            return None
        ev = ProductSupplierEvent(
            id_product=product_id, id_supplier=supplier_id, price=price, stock=stock,
            supplier_partnumber=supplier_partnumber, feed_run_id=feed_run_id,
            reason="init" if last is None else "change",
        )
        self.db.add(ev); self.db.flush(); return ev

    def mark_eol_for_unseen_items(self, *, feed_id: int, supplier_id: int, feed_run_id: int) -> int:
        stale: List[SupplierItem] = self.db.execute(
            select(SupplierItem).where(
                SupplierItem.feed_id==feed_id,
                or_(SupplierItem.last_seen_run_id.is_(None),
                    SupplierItem.last_seen_run_id != feed_run_id))
        ).scalars().all()
        if not stale: return 0
        marked = 0
        for it in stale:
            if not it.gtin: continue
            pid = self.db.scalar(select(Product.id).where(Product.gtin==it.gtin))
            if not pid: continue
            last = self.last_for(pid, supplier_id)
            if last and last.reason == "eol":
                continue
            ev = ProductSupplierEvent(
                id_product=pid, id_supplier=supplier_id,
                price=(last.price if last else "0"), stock=0,
                supplier_partnumber=(last.supplier_partnumber if last else None),
                feed_run_id=feed_run_id, reason="eol",
            )
            self.db.add(ev); marked += 1
        self.db.flush()
        return marked
