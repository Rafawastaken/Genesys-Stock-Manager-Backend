# app/domains/catalog/usecases/brands/list_brands.py
from __future__ import annotations
from collections.abc import Sequence

from app.infra.uow import UoW
from app.models.brand import Brand
from app.repositories.brand_repo import BrandRepository


def execute(
    uow: UoW, *, search: str | None, page: int, page_size: int
) -> tuple[Sequence[Brand], int]:
    repo = BrandRepository(uow.db)
    return repo.search_paginated(search, page, page_size)
