# app/domains/catalog/usecases/categories/list_categories.py
from __future__ import annotations

from app.infra.uow import UoW
from app.domains.catalog.repos import CategoryReadRepository


def execute(uow: UoW, *, search: str | None, page: int, page_size: int):
    repo = CategoryReadRepository(uow.db)
    return repo.list(q=search, page=page, page_size=page_size)
