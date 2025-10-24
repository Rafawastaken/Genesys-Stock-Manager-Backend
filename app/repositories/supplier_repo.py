# app/repositories/supplier_repo.py
from typing import Optional, Sequence, Tuple
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.repositories.base import Repository
from app.models.supplier import Supplier

class SupplierRepository(Repository[Supplier]):
    def __init__(self, db: Session):
        super().__init__(db, Supplier)

    def get_by_name_ci(self, name: str) -> Optional[Supplier]:
        return self.db.scalar(select(Supplier).where(func.lower(Supplier.name) == name.lower()))

    def search_paginated(self, search: Optional[str], page: int, page_size: int) -> Tuple[Sequence[Supplier], int]:
        q = select(Supplier)
        if search:
            like = f"%{search.strip()}%"
            q = q.where(Supplier.name.ilike(like))
        total = self.db.scalar(select(func.count()).select_from(q.subquery())) or 0
        rows = self.db.execute(
            q.order_by(Supplier.name.asc())
             .offset((page - 1) * page_size)
             .limit(page_size)
        ).scalars().all()
        return rows, int(total)

    def delete_by_id(self, supplier_id: int) -> bool:
        entity = self.get(supplier_id)  # vem do Repository base
        if not entity:
            return False
        self.delete(entity)             # usa delete(entity) do base
        return True
