# app/services/queries/mappers/get_mapper.py
from __future__ import annotations
import json
from app.infra.uow import UoW
from app.schemas.mappers import FeedMapperOut

def handle(uow: UoW, feed_id: int) -> FeedMapperOut:
    e = uow.mappers.get_or_create(feed_id)
    try:
        profile = json.loads(e.profile_json) if e.profile_json else {}
    except Exception:
        profile = {}
    return FeedMapperOut(
        id=e.id, feed_id=e.feed_id, profile=profile, version=e.version,
        created_at=e.created_at, updated_at=e.updated_at
    )
