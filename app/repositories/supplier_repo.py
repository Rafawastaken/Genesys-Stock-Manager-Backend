# app/repositories/supplier_repo.py
from __future__ import annotations
from typing import Optional, Tuple, Sequence
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.models.supplier import Supplier
from app.schemas.suppliers import SupplierCreate

class SupplierRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, id_supplier: int) -> Optional[Supplier]:
        return self.db.get(Supplier, id_supplier)

    def get_by_name(self, name: str) -> Optional[Supplier]:
        if not name: return None
        return self.db.scalar(select(Supplier).where(Supplier.name == name))

    def create(self, data: SupplierCreate) -> Supplier:
        e = Supplier(
            name=(data.name or "").strip(),
            active=data.active if data.active is not None else True,
            logo_image=(data.logo_image or None),
            contact_name=(data.contact_name or None),
            contact_email=(data.contact_email or None),
            contact_phone=(data.contact_phone or None),
            margin=(data.margin or 0.0),
            country=(data.country or None),
        )
        self.db.add(e)
        self.db.flush()
        return e

    def add(self, entity: Supplier) -> None:
        self.db.add(entity)
        self.db.flush()

    def delete(self, entity: Supplier) -> None:
        self.db.delete(entity)
        # sem flush/commit aqui

    def search_paginated(self, search: Optional[str], page: int, page_size: int) -> Tuple[Sequence[Supplier], int]:
        base = select(Supplier)
        if search:
            like = f"%{search.strip()}%"
            base = base.where(Supplier.name.ilike(like))
        total = self.db.scalar(select(func.count()).select_from(base.subquery())) or 0
        rows = self.db.execute(base.order_by(Supplier.created_at.desc()).limit(page_size).offset((page-1)*page_size)).scalars().all()
        return rows, int(total)
