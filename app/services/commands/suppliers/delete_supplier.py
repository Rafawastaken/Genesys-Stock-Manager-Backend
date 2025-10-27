# app/services/commands/suppliers/delete_supplier.py
from app.infra.uow import UoW
from app.repositories.supplier_repo import SupplierRepository

def handle(uow: UoW, *, supplier_id: int) -> None:
    repo = SupplierRepository(uow.db)
    supplier = repo.get(supplier_id)
    if not supplier:
        raise ValueError("SUPPLIER_NOT_FOUND")

    try:
        repo.delete(supplier)
        uow.commit()          # 👈 commands commit
    except Exception:
        uow.rollback()
        raise