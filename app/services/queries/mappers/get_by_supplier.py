# app/services/queries/mappers/get_by_supplier.py

from __future__ import annotations
import json

from app.infra.uow import UoW
from app.repositories.mapper_repo import MapperRepository
from app.schemas.mappers import FeedMapperOut

def handle(uow: UoW, *, supplier_id:int) -> FeedMapperOut:
    repo = MapperRepository(uow.db)
    e = repo.get_by_supplier(supplier_id)
    if not e:
        raise ValueError("MAPPER_NOT_FOUND")

    try:
        profile = json.loads(e.profile_json) if e.profile_json else {}
    except Exception:
        profile = {}

    return FeedMapperOut(
        id = e.id,
        feed_id = e.feed_id,
        profile = profile,
        version = e.version,
        created_at = e.created_at,
        updated_at = e.updated_at,
    )