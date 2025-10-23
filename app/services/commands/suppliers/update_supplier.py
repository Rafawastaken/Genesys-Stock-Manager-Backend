from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.infra.uow import UoW
from app.repositories.supplier_repo import SupplierRepository
from app.schemas.suppliers import SupplierUpdate

def handle(uow: UoW, *, supplier_id: int, data: SupplierUpdate):
    repo = SupplierRepository(uow.db)
    try:
        if hasattr(repo, "update"):
            entity = repo.update(supplier_id, data)
        else:
            # fallback manual
            entity = repo.get(supplier_id) if hasattr(repo, "get") else uow.db.get(repo.model, supplier_id)  # type: ignore
            if entity is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")

            # aplica apenas campos fornecidos
            for field in ("name","active","logo_image","contact_name","contact_email","contact_phone","margin","country"):
                if getattr(data, field, None) is not None:
                    setattr(entity, field, getattr(data, field))

        uow.commit()
        return entity

    except IntegrityError:
        uow.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Supplier name already exists",
        )
