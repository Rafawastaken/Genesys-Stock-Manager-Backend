# app/repositories/mapper_repo.py
from __future__ import annotations
import json
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.feed_mapper import FeedMapper
from app.models.supplier_feed import SupplierFeed  # 👈 importar para o join

class MapperRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, id_mapper: int) -> Optional[FeedMapper]:
        return self.db.get(FeedMapper, id_mapper)

    def get_by_feed(self, id_feed: int) -> Optional[FeedMapper]:
        return self.db.scalar(select(FeedMapper).where(FeedMapper.id_feed == id_feed))

    def get_by_supplier(self, id_supplier: int) -> Optional[FeedMapper]:
        # SupplierFeed.id_supplier é unique → devolve no máx. 1 Feed → 1 Mapper
        stmt = (
            select(FeedMapper)
            .join(SupplierFeed, FeedMapper.id_feed == SupplierFeed.id)
            .where(SupplierFeed.id_supplier == id_supplier)
        )
        return self.db.scalar(stmt)

    def get_or_create_by_feed(self, id_feed: int) -> FeedMapper:
        m = self.get_by_feed(id_feed)
        if m:
            return m
        m = FeedMapper(id_feed=id_feed, profile_json="{}", version=1)
        self.db.add(m)
        self.db.flush()
        return m

    def get_profile(self, id_feed: int) -> Dict[str, Any]:
        m = self.get_or_create_by_feed(id_feed)
        try:
            return json.loads(m.profile_json) if m.profile_json else {}
        except Exception:
            return {}

    def upsert_profile(self, id_feed: int, profile: Dict[str, Any], *, bump_version: bool = True) -> FeedMapper:
        m = self.get_by_feed(id_feed)
        creating = m is None
        if creating:
            m = FeedMapper(id_feed=id_feed, version=1)
            self.db.add(m)

        m.profile_json = json.dumps(profile, ensure_ascii=False)
        if not creating and bump_version:
            m.version = (m.version or 0) + 1
        elif creating and m.version is None:
            m.version = 1

        self.db.flush()
        return m
