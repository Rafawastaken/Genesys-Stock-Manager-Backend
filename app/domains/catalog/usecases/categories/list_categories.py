# app/domains/catalog/usecases/categories/list_categories.py
from __future__ import annotations
from collections.abc import Sequence

from app.infra.uow import UoW
from app.models.category import Category
from app.repositories.category_repo import CategoryRepository


def execute(
    uow: UoW, *, search: str | None, page: int, page_size: int
) -> tuple[Sequence[Category], int]:
    repo = CategoryRepository(uow.db)
    return repo.list(q=search, page=page, page_size=page_size)
