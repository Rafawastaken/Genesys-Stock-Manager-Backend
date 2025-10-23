from __future__ import annotations
from fastapi import HTTPException, status

from app.infra.uow import UoW
from app.repositories.supplier_repo import SupplierRepository

def handle(uow: UoW, *, supplier_id: int) -> None:
    repo = SupplierRepository(uow.db)
    if hasattr(repo, "delete"):
        repo.delete(supplier_id)
        uow.commit()
        return

    # fallback manual
    entity = repo.get(supplier_id) if hasattr(repo, "get") else None
    if entity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")

    uow.db.delete(entity)
    uow.commit()
