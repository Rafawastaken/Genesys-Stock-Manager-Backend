# app/services/queries/suppliers/list_suppliers.py
# This module provides a service to list suppliers with optional search and pagination.

from __future__ import annotations
from typing import Optional, Tuple, Sequence
from app.infra.uow import UoW
from app.repositories.supplier_repo import SupplierRepository
from app.models.supplier import Supplier

def handle(uow: UoW, *, search: Optional[str], page: int, page_size: int) -> Tuple[Sequence[Supplier], int]:
    repo = SupplierRepository(uow.db)
    return repo.search_paginated(search, page, page_size)
