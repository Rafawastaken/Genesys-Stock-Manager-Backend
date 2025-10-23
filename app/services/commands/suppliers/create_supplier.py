from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.infra.uow import UoW
from app.repositories.supplier_repo import SupplierRepository
from app.schemas.suppliers import SupplierCreate
from app.models.supplier import Supplier

def handle(uow: UoW, *, data: SupplierCreate):
    """
    Cria um fornecedor e faz commit via UoW.
    Usa repo.create() se existir; fallback para repo.add(entity).
    """
    repo = SupplierRepository(uow.db)

    try:
        if hasattr(repo, "create"):
            entity = repo.create(data)  # o repo trata do model internamente
        else:
            # fallback: construir a entity aqui
            entity = Supplier(
                name=data.name.strip(),
                active=data.active if data.active is not None else True,
                logo_image=(data.logo_image or None),
                contact_name=(data.contact_name or None),
                contact_email=(data.contact_email or None),
                contact_phone=(data.contact_phone or None),
                margin=(data.margin or 0.0),
                country=(data.country or None),
            )
            # alguns repos expõem add(); noutros podes usar uow.db.add(entity)
            add = getattr(repo, "add", None)
            if callable(add):
                add(entity)
            else:
                uow.db.add(entity)

        uow.commit()
        # Devolver a entity para FastAPI serializar com response_model
        return entity

    except IntegrityError:
        uow.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Supplier name already exists",
        )
