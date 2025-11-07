# app/repositories/supplier_feed_repo.py  (ou onde tens o repo)
from __future__ import annotations
from typing import Any
from collections.abc import Callable

from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import Conflict, InvalidArgument
from app.models.supplier_feed import SupplierFeed


def _norm_url(url: str | None) -> str | None:
    if url is None:
        return None
    u = url.strip()
    return u or None


class SupplierFeedRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, id_feed: int) -> SupplierFeed | None:
        return self.db.get(SupplierFeed, id_feed)

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

    def _validate_payload(self, e: SupplierFeed) -> None:
        # kind é opcional se não usares, ajusta conforme teu modelo
        if not e.format or e.format.lower() not in ("json", "csv"):
            raise InvalidArgument("Feed format must be 'json' or 'csv'") from None
        if not e.url or not _norm_url(e.url):
            raise InvalidArgument("Feed URL is empty") from None
        if e.format.lower() == "csv":
            delim = e.csv_delimiter or ","
            if len(delim) != 1:
                raise InvalidArgument("csv_delimiter must be a single character") from None
            e.csv_delimiter = delim
        # normalização final
        e.url = _norm_url(e.url)

    def upsert_for_supplier(
        self,
        id_supplier: int,
        mutate: Callable[[SupplierFeed], Any],
    ) -> SupplierFeed:
        """
        Atualiza se já existir feed para o supplier; caso contrário cria.
        Converte IntegrityError em Conflict com mensagem explícita.
        """
        entity = self.get_by_supplier(id_supplier)
        creating = False
        if entity is None:
            entity = SupplierFeed(id_supplier=id_supplier)
            creating = True

        # aplicar mutações vindas do usecase
        mutate(entity)
        # defaults suaves
        if entity.format:
            entity.format = entity.format.lower()
        if entity.csv_delimiter is None and entity.format == "csv":
            entity.csv_delimiter = ","

        self._validate_payload(entity)

        if creating:
            self.db.add(entity)

        try:
            self.db.flush()
            return entity
        except IntegrityError as e:
            self.db.rollback()
            msg = str(getattr(e, "orig", e))

            # mapeia nomes das constraints que tiveres (ajusta aos teus)
            if "ux_supplier_feed_supplier" in msg or "supplier_feed_id_supplier_key" in msg:
                raise Conflict("A feed already exists for this supplier") from None
            if "ux_supplier_feed_url_ci" in msg or ("unique" in msg and "url" in msg):
                # ver se é mesmo por URL (e quem é o dono)
                other = self.get_by_url_ci(entity.url or "")
                if other and other.id_supplier != id_supplier:
                    raise Conflict("This feed URL is already used by another supplier") from None
                raise Conflict("This feed URL already exists") from None
            # fallback
            raise
