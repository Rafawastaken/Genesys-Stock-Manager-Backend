# app/repositories/supplier_item_repo.py
# repository for SupplierItem model

import hashlib
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from .base import Repository
from app.models.supplier_item import SupplierItem

class SupplierItemRepository(Repository[SupplierItem]):
    def __init__(self, db: Session): super().__init__(db, SupplierItem)

    @staticmethod
    def _fp(price: str, stock: int) -> str:
        return hashlib.sha256(f"{price}|{stock}".encode()).hexdigest()

    def upsert(self, *, feed_id: int, sku: str, price: str, stock: int,
               gtin: Optional[str], partnumber: Optional[str], last_seen_run_id: Optional[int]) -> SupplierItem:
        it = self.db.scalar(select(SupplierItem).where(SupplierItem.feed_id==feed_id, SupplierItem.sku==sku))
        fp = self._fp(price, stock)
        if it:
            changed = (it.price!=price or it.stock!=stock or it.gtin!=gtin or
                       it.partnumber!=partnumber or it.fingerprint!=fp or it.last_seen_run_id!=last_seen_run_id)
            if changed:
                it.price=price; it.stock=stock; it.gtin=gtin; it.partnumber=partnumber
                it.fingerprint=fp; it.last_seen_run_id=last_seen_run_id
            return it
        it = SupplierItem(feed_id=feed_id, sku=sku, gtin=gtin, partnumber=partnumber,
                          price=price, stock=stock, fingerprint=fp, last_seen_run_id=last_seen_run_id)
        self.db.add(it); self.db.flush()
        return it
