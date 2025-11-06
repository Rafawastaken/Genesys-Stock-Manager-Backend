# app/domains/procurement/usecases/feeds/delete_supplier_feed.py
from __future__ import annotations

from sqlalchemy.exc import IntegrityError

from app.core.errors import Conflict, NotFound
from app.domains.procurement.repos import SupplierFeedRepository
from app.infra.uow import UoW


def execute(uow: UoW, *, id_supplier: int) -> None:
    repo = SupplierFeedRepository(uow.db)
    feed = repo.get_by_supplier(id_supplier)
    if not feed:
        raise NotFound("Feed not found for supplier")

    try:
        repo.delete(feed)  # espera o ORM entity
        uow.commit()
    except IntegrityError:
        uow.rollback()
        # FK constraints ou regras de integridade
        raise Conflict("Cannot delete feed due to integrity constraints")
