# app/repositories/supplier_feed_repo.py
from __future__ import annotations
from typing import Optional, Callable
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.supplier_feed import SupplierFeed


class SupplierFeedRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, feed_id: int) -> Optional[SupplierFeed]:
        return self.db.get(SupplierFeed, feed_id)

    def get_by_supplier(self, supplier_id: int) -> Optional[SupplierFeed]:
        return self.db.scalar(select(SupplierFeed).where(SupplierFeed.supplier_id == supplier_id))

    def upsert_for_supplier(self, supplier_id: int, mutate: Callable[[SupplierFeed], None]) -> SupplierFeed:
        entity = self.get_by_supplier(supplier_id)
        creating = entity is None
        if creating:
            entity = SupplierFeed(supplier_id=supplier_id)
            self.db.add(entity)

        mutate(entity)
        self.db.flush()          # 👈 sem commit
        return entity

    def delete_by_supplier(self, supplier_id: int) -> bool:
        entity = self.get_by_supplier(supplier_id)
        if not entity:
            return False
        self.db.delete(entity)
        self.db.flush()          # 👈 sem commit
        return True

