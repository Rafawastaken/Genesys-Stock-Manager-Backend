# app/repositories/supplier_feed_repo.py
from __future__ import annotations
from typing import Optional, Callable
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.supplier_feed import SupplierFeed


class SupplierFeedRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, id_feed: int) -> Optional[SupplierFeed]:
        return self.db.get(SupplierFeed, id_feed)

    def get_by_supplier(self, id_supplier: int) -> Optional[SupplierFeed]:
        return self.db.scalar(select(SupplierFeed).where(SupplierFeed.id_supplier == id_supplier))

    def upsert_for_supplier(self, id_supplier: int, mutate: Callable[[SupplierFeed], None]) -> SupplierFeed:
        entity = self.get_by_supplier(id_supplier)
        creating = entity is None
        if creating:
            entity = SupplierFeed(id_supplier=id_supplier)
            self.db.add(entity)

        mutate(entity)
        self.db.flush()          # 👈 sem commit
        return entity

    def delete_by_supplier(self, id_supplier: int) -> bool:
        entity = self.get_by_supplier(id_supplier)
        if not entity:
            return False
        self.db.delete(entity)
        self.db.flush()          # 👈 sem commit
        return True

