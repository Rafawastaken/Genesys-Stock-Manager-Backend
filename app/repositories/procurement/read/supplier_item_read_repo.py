from __future__ import annotations

from collections.abc import Sequence
from sqlalchemy import func, select, and_
from sqlalchemy.orm import Session

from app.core.errors import NotFound
from app.core.normalize import normalize_key_ci
from app.models.supplier import Supplier

MAX_NAME_LEN = 200


class SupplierItemReadRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, id_supplier: int) -> Supplier | None:
        return self.db.get(Supplier, id_supplier)

    def get_required(self, id_supplier: int) -> Supplier:
        e = self.get(id_supplier)
        if not e:
            raise NotFound("Supplier not found")
        return e

    def get_by_name(self, name: str) -> Supplier | None:
        key = normalize_key_ci(name, MAX_NAME_LEN)
        if not key:
            return None
        return (
            self.db.execute(
                select(Supplier).where(func.lower(func.btrim(Supplier.name)) == key).limit(1)
            )
            .scalars()
            .first()
        )

    def search_paginated(
        self, search: str | None, page: int, page_size: int
    ) -> tuple[Sequence[Supplier], int]:
        page = max(1, page)
        page_size = max(1, min(page_size, 100))

        stmt = select(Supplier)
        filters = []
        if search:
            like = f"%{search.strip()}%"
            filters.append(func.btrim(Supplier.name).ilike(like))
        if filters:
            stmt = stmt.where(and_(*filters))

        total = (
            self.db.scalar(
                (select(func.count()).select_from(Supplier).where(and_(*filters)))
                if filters
                else (select(func.count()).select_from(Supplier))
            )
            or 0
        )

        # Ordenação estável por nome CI + id
        stmt = stmt.order_by(
            func.lower(func.btrim(Supplier.name)).asc(),
            Supplier.id.asc(),
        )

        rows = self.db.execute(stmt.limit(page_size).offset((page - 1) * page_size)).scalars().all()
        return rows, int(total)
