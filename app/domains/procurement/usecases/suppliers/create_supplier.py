from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.infra.uow import UoW
from app.domains.procurement.repos import SupplierRepository
from app.schemas.suppliers import SupplierCreate
from app.models.supplier import Supplier


def execute(uow: UoW, data: SupplierCreate):
    """
    Create a supplier and commit via UoW.
    Prefer repo.create(data) if available; fallback to building the ORM entity and adding it.
    Errors are always in English.
    """
    repo = SupplierRepository(uow.db)

    try:
        # Preferred path: repository exposes a create(data)
        create = getattr(repo, "create", None)
        if callable(create):
            entity = create(data)
        else:
            # Fallback: build the model here and add via repo.add(...) or session.add(...)
            entity = Supplier(
                name=(data.name or "").strip(),
                active=data.active if data.active is not None else True,
                logo_image=(data.logo_image or None),
                contact_name=(data.contact_name or None),
                contact_email=(data.contact_email or None),
                contact_phone=(data.contact_phone or None),
                margin=(data.margin or 0.0),
                country=(data.country or None),
            )

            add = getattr(repo, "add", None)
            if callable(add):
                add(entity)
            else:
                uow.db.add(entity)

        uow.commit()
        # Return the ORM entity; your response_model can serialize from attributes
        return entity

    except IntegrityError:
        uow.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Supplier name already exists",
        )
    except HTTPException:
        # Bubble FastAPI HTTP errors as-is
        uow.rollback()
        raise
    except Exception as e:
        uow.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not create supplier: {e}",
        )
