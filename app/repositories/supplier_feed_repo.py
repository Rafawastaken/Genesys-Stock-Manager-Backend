# app/repositories/supplier_feed_repo.py
from __future__ import annotations

from collections.abc import Callable

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.supplier_feed import SupplierFeed


class SupplierFeedRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, id_feed: int) -> SupplierFeed | None:
        return self.db.get(SupplierFeed, id_feed)

    def get_by_supplier(self, id_supplier: int) -> SupplierFeed | None:
        return self.db.scalar(select(SupplierFeed).where(SupplierFeed.id_supplier == id_supplier))

    def upsert_for_supplier(
        self, id_supplier: int, mutate: Callable[[SupplierFeed], None]
    ) -> SupplierFeed:
        e = self.get_by_supplier(id_supplier)
        if not e:
            e = SupplierFeed(id_supplier=id_supplier)
            self.db.add(e)
            self.db.flush()  # para ter id
        mutate(e)
        self.db.add(e)
        self.db.flush()
        return e

    def delete_by_supplier(self, id_supplier: int) -> int:
        res = self.db.execute(delete(SupplierFeed).where(SupplierFeed.id_supplier == id_supplier))
        # não faz commit aqui
        return res.rowcount or 0
