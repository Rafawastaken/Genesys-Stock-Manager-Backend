# app/repositories/product_event_repo.py
from __future__ import annotations
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.product_supplier_event import ProductSupplierEvent
from app.models.supplier_item import SupplierItem

class ProductEventRepository:
    def __init__(self, db: Session):
        self.db = db

    def record_from_item_change(
        self,
        *,
        id_product: int,
        id_supplier: int,
        gtin: Optional[str],
        new_price: str,
        new_stock: int,
        created: bool,
        changed: bool,
        id_feed_run: int,
    ) -> int:
        if not (created or changed):
            return 0

        reason = "init" if created else "change"
        self.db.add(ProductSupplierEvent(
            id_product=id_product,
            id_supplier=id_supplier,
            gtin=gtin,
            price=new_price,
            stock=new_stock,
            id_feed_run=id_feed_run,
            reason=reason,
        ))
        return 1

    def mark_eol_for_unseen_items(self, *, id_feed: int, id_supplier: int, id_feed_run: int) -> int:
        unseen = self.db.scalars(
            select(SupplierItem).where(
                SupplierItem.id_feed == id_feed,
                SupplierItem.id_feed_run != id_feed_run,
            )
        ).all()

        count = 0
        for it in unseen:
            self.db.add(ProductSupplierEvent(
                id_product=it.id_product,
                id_supplier=id_supplier,
                gtin=it.gtin,
                price=it.price,
                stock=0,
                id_feed_run=id_feed_run,
                reason="eol",
            ))
            count += 1
        return count
