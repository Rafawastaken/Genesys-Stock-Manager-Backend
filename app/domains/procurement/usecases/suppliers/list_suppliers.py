from __future__ import annotations

from collections.abc import Sequence

from app.domains.procurement.repos import SupplierReadRepository
from app.infra.uow import UoW
from app.models.supplier import Supplier


def execute(
    uow: UoW, *, search: str | None, page: int, page_size: int
) -> tuple[Sequence[Supplier], int]:
    repo = SupplierReadRepository(uow.db)
    return repo.search_paginated(search, page, page_size)
