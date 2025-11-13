from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import InvalidArgument
from app.models.feed_mapper import FeedMapper


class MapperWriteRepository:
    def __init__(self, db: Session):
        self.db = db

    def _get_by_feed(self, id_feed: int) -> FeedMapper | None:
        stmt = select(FeedMapper).where(FeedMapper.id_feed == id_feed).limit(1)
        return self.db.execute(stmt).scalars().first()

    def get_or_create_by_feed(self, id_feed: int) -> FeedMapper:
        m = self._get_by_feed(id_feed)
        if m is not None:
            return m

        m = FeedMapper(id_feed=id_feed, profile_json="{}", version=1)
        self.db.add(m)
        self.db.flush()
        return m

    def set_profile(
        self,
        id_feed: int,
        profile: dict[str, Any],
        *,
        bump_version: bool = True,
    ) -> FeedMapper:
        if not isinstance(profile, dict):
            raise InvalidArgument("Mapper profile must be an object (dict)")

        m = self._get_by_feed(id_feed)
        creating = m is None

        if creating:
            m = FeedMapper(id_feed=id_feed, version=1)
            self.db.add(m)

        m.profile_json = json.dumps(profile, ensure_ascii=False)

        if creating and m.version is None:
            m.version = 1
        elif not creating and bump_version:
            m.version = (m.version or 0) + 1

        self.db.flush()
        return m

    # alias de compatibilidade com o nome que tinhas
    def upsert_profile(
        self,
        id_feed: int,
        profile: dict[str, Any],
        *,
        bump_version: bool = True,
    ) -> FeedMapper:
        return self.set_profile(id_feed, profile, bump_version=bump_version)
