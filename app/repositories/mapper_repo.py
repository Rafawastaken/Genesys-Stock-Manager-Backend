# app/repositories/mapper_repo.py
from __future__ import annotations

import json
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.feed_mapper import FeedMapper


class MapperRepository:
    """
    Repositório para FeedMapper (perfil de mapeamento por feed).
    Mantém a lógica de acesso/CRUD encapsulada.
    """

    def __init__(self, db: Session):
        self.db = db

    # ---------- READ ----------
    def get(self, mapper_id: int) -> Optional[FeedMapper]:
        return self.db.get(FeedMapper, mapper_id)

    def get_by_feed(self, feed_id: int) -> Optional[FeedMapper]:
        stmt = select(FeedMapper).where(FeedMapper.feed_id == feed_id)
        return self.db.scalar(stmt)

    def get_or_create_by_feed(self, feed_id: int) -> FeedMapper:
        m = self.get_by_feed(feed_id)
        if m:
            return m
        m = FeedMapper(feed_id=feed_id, profile_json="{}", version=1)
        self.db.add(m)
        self.db.commit()
        self.db.refresh(m)
        return m

    # ---------- PROFILE HELPERS ----------
    def get_profile(self, feed_id: int) -> Dict[str, Any]:
        m = self.get_or_create_by_feed(feed_id)
        try:
            return json.loads(m.profile_json) if m.profile_json else {}
        except Exception:
            return {}

    def upsert_profile(
        self,
        feed_id: int,
        profile: Dict[str, Any],
        *,
        bump_version: bool = True,
    ) -> FeedMapper:
        m = self.get_by_feed(feed_id)
        creating = m is None
        if creating:
            m = FeedMapper(feed_id=feed_id, version=1)

        m.profile_json = json.dumps(profile, ensure_ascii=False)
        if not creating and bump_version:
            m.version = (m.version or 0) + 1
        elif creating and m.version is None:
            m.version = 1

        if creating:
            self.db.add(m)
        self.db.commit()
        self.db.refresh(m)
        return m


# Alias opcional para compatibilidade com nomes antigos
MapperRepo = MapperRepository
