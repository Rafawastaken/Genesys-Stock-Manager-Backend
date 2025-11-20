from __future__ import annotations

from datetime import datetime
from sqlalchemy.orm import Session

from app.models.catalog_update_stream import CatalogUpdateStream


class CatalogUpdateStreamReadRepository:
    """
    Repositório de leitura para a fila de atualização de catálogo.

    Responsabilidade:
    - Consultar eventos (pending, done, failed) sem alterar estado.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def list_pending_for_claim(
        self,
        *,
        limit: int,
        min_priority: int | None = None,
    ) -> list[CatalogUpdateStream]:
        """
        Devolve até `limit` eventos em estado `pending`, ordenados por:
        - priority DESC
        - available_at ASC
        - created_at ASC

        NÃO altera estado (não marca como processing).
        """
        now = datetime.utcnow()

        q = self.db.query(CatalogUpdateStream).filter(
            CatalogUpdateStream.status == "pending",
            CatalogUpdateStream.available_at <= now,
        )

        if min_priority is not None:
            q = q.filter(CatalogUpdateStream.priority >= min_priority)

        q = q.order_by(
            CatalogUpdateStream.priority.desc(),
            CatalogUpdateStream.available_at.asc(),
            CatalogUpdateStream.created_at.asc(),
        ).limit(limit)

        return q.all()
