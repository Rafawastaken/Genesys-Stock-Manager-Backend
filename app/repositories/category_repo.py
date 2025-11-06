# app/repositories/category_repo.py
from __future__ import annotations
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.category import Category
from app.core.errors import InvalidArgument, NotFound

class CategoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, id_category: int) -> Optional[Category]:
        return self.db.get(Category, id_category)

    def get_required(self, id_category: int) -> Category:
        c = self.get(id_category)
        if not c:
            raise NotFound("Category not found")
        return c

    def get_by_name(self, name: str) -> Optional[Category]:
        if not name:
            return None
        return self.db.scalar(select(Category).where(Category.name == name))

    def get_or_create(self, name: str) -> Category:
        n = (name or "").strip()
        if not n:
            raise InvalidArgument("Category name is empty")
        c = self.get_by_name(n)
        if c:
            return c
        c = Category(name=n)
        self.db.add(c)
        self.db.flush()  # sem commit
        return c
