# app/services/commands/mappers/put_mapper.py
from __future__ import annotations
import json
from app.infra.uow import UoW
from app.schemas.mappers import FeedMapperUpsert, FeedMapperOut

def handle(uow: UoW, *, feed_id: int, payload: FeedMapperUpsert) -> FeedMapperOut:
    def mutate(e, creating: bool):
        e.profile_json = json.dumps(payload.profile or {}, ensure_ascii=False)
        if payload.bump_version:
            # no create: começa em 1; senão incrementa
            e.version = (e.version or 0) + (0 if creating else 1) if not creating else 1

    e = uow.mappers.upsert(feed_id, mutate)
    try:
        profile = json.loads(e.profile_json) if e.profile_json else {}
    except Exception:
        profile = {}
    return FeedMapperOut(
        id=e.id, feed_id=e.feed_id, profile=profile, version=e.version,
        created_at=e.created_at, updated_at=e.updated_at
    )
