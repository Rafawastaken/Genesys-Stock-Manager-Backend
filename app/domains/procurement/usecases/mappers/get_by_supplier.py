from __future__ import annotations
import json

from app.core.errors import NotFound
from app.infra.uow import UoW
from app.domains.procurement.repos import MapperRepository
from app.schemas.mappers import FeedMapperOut

def execute(uow: UoW, *, id_supplier: int) -> FeedMapperOut:
    repo = MapperRepository(uow.db)
    e = repo.get_by_supplier(id_supplier)
    if not e:
        raise NotFound("Mapper not found")
    try:
        profile = json.loads(e.profile_json) if getattr(e, "profile_json", None) else {}
    except Exception:
        profile = {}
    return FeedMapperOut(
        id=e.id,
        id_feed=e.id_feed,
        profile=profile,
        version=e.version,
        created_at=e.created_at,
        updated_at=e.updated_at,
    )
