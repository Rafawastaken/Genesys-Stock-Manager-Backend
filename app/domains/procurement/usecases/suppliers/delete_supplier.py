# app/domains/procurement/usecases/suppliers/delete_supplier.py
from __future__ import annotations
from app.infra.uow import UoW
from app.domains.procurement.repos import SupplierRepository

def execute(uow: UoW, *, id_supplier: int) -> None:
    repo = SupplierRepository(uow.db)

    supplier = repo.get(id_supplier)
    if not supplier:
        # keep the exact contract; message already in English
        raise ValueError("SUPPLIER_NOT_FOUND")

    try:
        repo.delete(supplier)   # delete expects the ORM entity (as in your original command)
        uow.commit()
    except Exception:
        uow.rollback()
        raise
