# app/domains/procurement/usecases/mappers/get_by_supplier.py
from __future__ import annotations

from app.core.errors import NotFound
from app.domains.procurement.repos import MapperReadRepository
from app.infra.uow import UoW
from app.schemas.mappers import FeedMapperOut


def execute(uow: UoW, *, id_supplier: int) -> FeedMapperOut:
    repo = MapperReadRepository(uow.db)
    e = repo.get_by_supplier(id_supplier)
    if not e:
        raise NotFound("Mapper not found")
    return FeedMapperOut.from_entity(e)
