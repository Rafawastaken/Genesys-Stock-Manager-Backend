# app/domains/procurement/usecases/suppliers/create_supplier.py
from __future__ import annotations

from sqlalchemy.exc import IntegrityError

from app.core.errors import BadRequest, Conflict, InvalidArgument  # << usa AppErrors
from app.domains.procurement.repos import SupplierWriteRepository
from app.infra.uow import UoW
from app.models.supplier import Supplier
from app.schemas.suppliers import SupplierCreate


def execute(uow: UoW, *, data: SupplierCreate) -> Supplier:
    """
    Create a supplier and commit via UoW.
    Prefers repo.create(data); falls back to building the ORM entity.
    Errors are domain AppErrors (handled by middleware).
    """
    # validação mínima
    name = (data.name or "").strip()
    if not name:
        raise InvalidArgument("Supplier name is required")

    repo = SupplierWriteRepository(uow.db)

    try:
        create = getattr(repo, "create", None)
        if callable(create):
            entity = create(data)
        else:
            entity = Supplier(
                name=name,
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
        return entity

    except IntegrityError as err:
        uow.rollback()
        # violação de unicidade, etc.
        raise Conflict("Supplier name already exists") from err
    except (InvalidArgument, Conflict, BadRequest):
        # repropaga AppErrors já mapeados
        uow.rollback()
        raise
    except Exception as err:
        uow.rollback()
        # não expor detalhes internos
        raise BadRequest("Could not create supplier") from err
