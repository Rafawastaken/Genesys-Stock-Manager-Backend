# app/repositories/category_repo.py
from __future__ import annotations

from sqlalchemy import select, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.errors import InvalidArgument
from app.models.category import Category
from app.core.normalize import normalize_simple, normalize_key_ci


MAX_NAME_LEN = 900


class CategoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_name(self, name: str) -> Category | None:
        key = normalize_key_ci(name, MAX_NAME_LEN)
        if not key:
            return None
        return (
            self.db.execute(
                select(Category).where(func.lower(func.btrim(Category.name)) == key).limit(1)
            )
            .scalars()
            .first()
        )

    def get_or_create(self, name: str) -> Category:
        shown = normalize_simple(name, MAX_NAME_LEN)
        key = normalize_key_ci(name, MAX_NAME_LEN)
        if not key:
            raise InvalidArgument("Category name is empty")

        existing = self.get_by_name(shown)
        if existing:
            return existing

        c = Category(name=shown)
        self.db.add(c)
        try:
            self.db.flush()
            return c
        except IntegrityError:
            self.db.rollback()
            again = self.get_by_name(shown)
            if again:
                return again
            raise

    def list(self, *, q: str | None, page: int, page_size: int):
        stmt = select(Category)
        if q:
            like = f"%{q.strip()}%"
            stmt = stmt.where(Category.name.ilike(like))
        stmt = stmt.order_by(Category.name.asc())

        total = self.db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()

        page = max(1, page)
        page_size = max(1, min(page_size, 100))
        rows = self.db.execute(stmt.limit(page_size).offset((page - 1) * page_size)).scalars().all()
        return rows, int(total)
