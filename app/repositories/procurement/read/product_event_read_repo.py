from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select, desc, func
from sqlalchemy.orm import Session

from app.models.product_supplier_event import ProductSupplierEvent


class ProductEventReadRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, id_event: int) -> ProductSupplierEvent | None:
        return self.db.get(ProductSupplierEvent, id_event)

    def list_by_product(
        self, id_product: int, *, limit: int = 100, offset: int = 0
    ) -> Sequence[ProductSupplierEvent]:
        stmt = (
            select(ProductSupplierEvent)
            .where(ProductSupplierEvent.id_product == id_product)
            .order_by(desc(ProductSupplierEvent.created_at), desc(ProductSupplierEvent.id))
            .limit(limit)
            .offset(offset)
        )
        return self.db.scalars(stmt).all()

    def list_recent_for_supplier(
        self, id_supplier: int, *, limit: int = 100, offset: int = 0
    ) -> Sequence[ProductSupplierEvent]:
        stmt = (
            select(ProductSupplierEvent)
            .where(ProductSupplierEvent.id_supplier == id_supplier)
            .order_by(desc(ProductSupplierEvent.created_at), desc(ProductSupplierEvent.id))
            .limit(limit)
            .offset(offset)
        )
        return self.db.scalars(stmt).all()

    def last_for_product_supplier(
        self, *, id_product: int, id_supplier: int
    ) -> ProductSupplierEvent | None:
        stmt = (
            select(ProductSupplierEvent)
            .where(
                ProductSupplierEvent.id_product == id_product,
                ProductSupplierEvent.id_supplier == id_supplier,
            )
            .order_by(desc(ProductSupplierEvent.created_at), desc(ProductSupplierEvent.id))
            .limit(1)
        )
        return self.db.scalars(stmt).first()

    def count_by_run(self, id_feed_run: int) -> int:
        stmt = (
            select(func.count())
            .select_from(ProductSupplierEvent)
            .where(ProductSupplierEvent.id_feed_run == id_feed_run)
        )
        return int(self.db.scalar(stmt) or 0)
