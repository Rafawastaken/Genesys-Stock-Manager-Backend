# app/repositories/brand_repo.py
from __future__ import annotations
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.brand import Brand

class BrandRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_name(self, name: str) -> Optional[Brand]:
        if not name:
            return None
        return self.db.scalar(select(Brand).where(Brand.name == name))

    def get_or_create(self, name: str) -> Brand:
        n = (name or "").strip()
        if not n:
            raise ValueError("brand name empty")
        b = self.get_by_name(n)
        if b:
            return b
        b = Brand(name=n)
        self.db.add(b)
        self.db.flush()
        return b
