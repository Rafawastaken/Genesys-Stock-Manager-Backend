# app/domains/procurement/usecases/mappers/put_mapper.py
# Function to upsert a feed mapper profile.

from __future__ import annotations
import json
from fastapi import HTTPException
from app.infra.uow import UoW
from app.domains.procurement.repos import MapperRepository
from app.schemas.mappers import FeedMapperUpsert, FeedMapperOut

def execute(uow: UoW, *, id_feed: int, payload: FeedMapperUpsert) -> FeedMapperOut:
    repo = MapperRepository(uow.db)
    try:
        entity = repo.upsert_profile(
            id_feed=id_feed,
            profile=payload.profile,
            bump_version=payload.bump_version,
        )
        uow.commit()
    except Exception as e:
        uow.rollback()
        raise HTTPException(status_code=400, detail=f"Could not upsert mapper: {e}")

    return FeedMapperOut(
        id=entity.id,
        id_feed=entity.id_feed,
        profile=json.loads(entity.profile_json) if entity.profile_json else {},
        version=entity.version or 1,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )
