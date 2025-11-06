# app/domains/procurement/usecases/suppliers/delete_supplier.py
from __future__ import annotations

from sqlalchemy.exc import IntegrityError

from app.infra.uow import UoW
from app.domains.procurement.repos import SupplierRepository
from app.core.errors import NotFound, Conflict, BadRequest


def execute(uow: UoW, *, id_supplier: int) -> None:
    repo = SupplierRepository(uow.db)

    supplier = repo.get(id_supplier)
    if not supplier:
        raise NotFound("Supplier not found")

    try:
        # repo.delete espera a entidade ORM
        repo.delete(supplier)
        uow.commit()
    except IntegrityError:
        uow.rollback()
        # FK em itens/feeds, etc.
        raise Conflict("Cannot delete supplier due to related records")
    except Exception:
        uow.rollback()
        # não expomos detalhes internos; middleware mapeia para {"code","detail"}
        raise BadRequest("Could not delete supplier")
