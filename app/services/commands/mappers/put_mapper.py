# app/services/commands/mappers/put_mapper.py
from __future__ import annotations
import json
from app.infra.uow import UoW
from app.repositories.mapper_repo import MapperRepository
from app.schemas.mappers import FeedMapperUpsert, FeedMapperOut

def handle(uow: UoW, *, id_feed: int, payload: FeedMapperUpsert) -> FeedMapperOut:
    repo = MapperRepository(uow.db)
    # repo espera um dict profile, não uma função
    entity = repo.upsert_profile(
        id_feed=id_feed,
        profile=payload.profile,
        bump_version=payload.bump_version,
    )
    # manter a semântica "commands fazem commit"
    uow.commit()

    return FeedMapperOut(
        id=entity.id,
        id_feed=entity.id_feed,
        profile=json.loads(entity.profile_json) if entity.profile_json else {},
        version=entity.version or 1,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )
