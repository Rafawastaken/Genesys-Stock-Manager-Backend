# app/domains/procurement/usecases/mappers/put_mapper.py
from __future__ import annotations
import json
from sqlalchemy.exc import IntegrityError

from app.infra.uow import UoW
from app.domains.procurement.repos import MapperRepository, SupplierFeedRepository
from app.schemas.mappers import FeedMapperUpsert, FeedMapperOut
from app.core.errors import InvalidArgument, NotFound, Conflict, BadRequest

def execute(uow: UoW, *, id_feed: int, payload: FeedMapperUpsert) -> FeedMapperOut:
    # validação mínima do payload
    if payload is None or payload.profile is None or not isinstance(payload.profile, dict):
        raise InvalidArgument("Mapper profile must be a non-empty object")

    # garantir que o feed existe
    feed_repo = SupplierFeedRepository(uow.db)
    feed = feed_repo.get(id_feed)
    if not feed:
        raise NotFound("Feed not found")

    repo = MapperRepository(uow.db)
    try:
        entity = repo.upsert_profile(
            id_feed=id_feed,
            profile=payload.profile,
            bump_version=payload.bump_version,
        )
        uow.commit()
    except IntegrityError:
        uow.rollback()
        raise Conflict("Could not upsert mapper due to integrity constraints")
    except Exception as e:
        uow.rollback()
        raise BadRequest("Could not upsert mapper")

    return FeedMapperOut(
        id=entity.id,
        id_feed=entity.id_feed,
        profile=json.loads(entity.profile_json) if entity.profile_json else {},
        version=entity.version or 1,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )
