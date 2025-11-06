# app/repositories/brand_repo.py
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import InvalidArgument, NotFound
from app.models.brand import Brand


class BrandRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, id_brand: int) -> Brand | None:
        return self.db.get(Brand, id_brand)

    def get_required(self, id_brand: int) -> Brand:
        b = self.get(id_brand)
        if not b:
            raise NotFound("Brand not found")
        return b

    def get_by_name(self, name: str) -> Brand | None:
        if not name:
            return None
        return self.db.scalar(select(Brand).where(Brand.name == name))

    def get_or_create(self, name: str) -> Brand:
        n = (name or "").strip()
        if not n:
            raise InvalidArgument("Brand name is empty")
        b = self.get_by_name(n)
        if b:
            return b
        b = Brand(name=n)
        self.db.add(b)
        self.db.flush()
        return b
