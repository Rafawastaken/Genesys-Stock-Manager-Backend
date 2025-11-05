from __future__ import annotations
from typing import Optional, Tuple, Sequence
from app.infra.uow import UoW
from app.domains.procurement.repos import SupplierRepository
from app.models.supplier import Supplier

def execute(uow: UoW, *, search: Optional[str], page: int, page_size: int) -> Tuple[Sequence[Supplier], int]:
    repo = SupplierRepository(uow.db)
    return repo.search_paginated(search, page, page_size)
