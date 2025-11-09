# app/repositories/category_repo.py
from __future__ import annotations

from sqlalchemy import select, func, and_
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
        # bounds
        page = max(1, page)
        page_size = max(1, min(page_size, 100))

        # base & filtros
        stmt = select(Category)
        filters = []
        if q:
            like = f"%{q.strip()}%"
            filters.append(func.btrim(Category.name).ilike(like))

        if filters:
            stmt = stmt.where(and_(*filters))

        # total (sem ORDER BY/LIMIT)
        total = (
            self.db.scalar(
                (select(func.count()).select_from(Category).where(and_(*filters)))
                if filters
                else (select(func.count()).select_from(Category))
            )
            or 0
        )

        # ordenação estável, case-insensitive
        stmt = stmt.order_by(
            func.lower(func.btrim(Category.name)).asc(),
            Category.id.asc(),
        )

        rows = self.db.execute(stmt.limit(page_size).offset((page - 1) * page_size)).scalars().all()
        return rows, int(total)
