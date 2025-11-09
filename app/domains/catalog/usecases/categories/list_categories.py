# app/domains/catalog/usecases/categories/list_categories.py
from __future__ import annotations

from app.infra.uow import UoW
from app.repositories.category_repo import CategoryRepository


def execute(uow: UoW, *, search: str | None, page: int, page_size: int):
    repo = CategoryRepository(uow.db)
    return repo.list(q=search, page=page, page_size=page_size)
