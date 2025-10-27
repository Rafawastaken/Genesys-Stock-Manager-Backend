# app/services/commands/suppliers/delete_supplier.py
from app.infra.uow import UoW
from app.repositories.supplier_repo import SupplierRepository

def handle(uow: UoW, *, id_supplier: int) -> None:
    repo = SupplierRepository(uow.db)
    supplier = repo.get(id_supplier)
    if not supplier:
        raise ValueError("SUPPLIER_NOT_FOUND")

    try:
        repo.delete(supplier)
        uow.commit()          # 👈 commands commit
    except Exception:
        uow.rollback()
        raise