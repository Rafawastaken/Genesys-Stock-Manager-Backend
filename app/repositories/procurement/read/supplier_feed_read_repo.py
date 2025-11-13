from __future__ import annotations

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.core.errors import NotFound
from app.models.supplier_feed import SupplierFeed


def _norm_url(url: str | None) -> str | None:
    if url is None:
        return None
    u = url.strip()
    return u or None


class SupplierFeedReadRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, id_feed: int) -> SupplierFeed | None:
        return self.db.get(SupplierFeed, id_feed)

    def get_required(self, id_feed: int) -> SupplierFeed:
        e = self.get(id_feed)
        if not e:
            raise NotFound("Feed not found")
        return e

    def get_by_supplier(self, id_supplier: int) -> SupplierFeed | None:
        return (
            self.db.execute(
                select(SupplierFeed).where(SupplierFeed.id_supplier == id_supplier).limit(1)
            )
            .scalars()
            .first()
        )

    def get_by_url_ci(self, url: str) -> SupplierFeed | None:
        u = _norm_url(url)
        if not u:
            return None
        return (
            self.db.execute(
                select(SupplierFeed)
                .where(
                    func.lower(func.btrim(SupplierFeed.url))
                    == func.lower(func.btrim(func.cast(u, SupplierFeed.url.type)))
                )
                .limit(1)
            )
            .scalars()
            .first()
        )
