from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.feed_mapper import FeedMapper
from app.models.supplier_feed import SupplierFeed


class MapperReadRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, id_mapper: int) -> FeedMapper | None:
        return self.db.get(FeedMapper, id_mapper)

    def get_by_feed(self, id_feed: int) -> FeedMapper | None:
        stmt = select(FeedMapper).where(FeedMapper.id_feed == id_feed).limit(1)
        return self.db.scalars(stmt).first()

    def get_by_supplier(self, id_supplier: int) -> FeedMapper | None:
        stmt = (
            select(FeedMapper)
            .join(SupplierFeed, FeedMapper.id_feed == SupplierFeed.id)
            .where(SupplierFeed.id_supplier == id_supplier)
            .limit(1)
        )
        return self.db.scalars(stmt).first()

    def profile_for_feed(self, id_feed: int) -> dict[str, Any] | None:
        """
        Lê o profile JSON do mapper; não cria nada se não existir.
        Retorna None se não houver mapper; {} se houver mas estiver vazio/parse falhar.
        """
        m = self.get_by_feed(id_feed)
        if not m:
            return None
        try:
            return json.loads(m.profile_json) if m.profile_json else {}
        except Exception:
            return {}
