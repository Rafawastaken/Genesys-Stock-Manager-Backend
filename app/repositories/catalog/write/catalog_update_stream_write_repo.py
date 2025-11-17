from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.catalog_update_stream import CatalogUpdateStream
from app.models.product import Product
from app.models.product_active_offer import ProductActiveOffer


class CatalogUpdateStreamWriteRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _build_payload(
        self,
        product: Product,
        active_offer: ProductActiveOffer | None,
        reason: str,
    ) -> dict[str, Any]:
        """
        Snapshot minimal mas suficiente para o módulo do PrestaShop aplicar:
        - dados "semânticos" do produto (sem duplicar id_product/id_ecommerce)
        - dados da oferta ativa
        - hint para shipping (id_supplier da active offer)
        """
        return {
            "reason": reason,
            "product": {
                # sem id_product / id_ecommerce aqui, já estão no evento
                "gtin": product.gtin,
                "partnumber": product.partnumber,
                "name": product.name,
                "margin": float(product.margin or 0),
                "is_enabled": product.is_enabled,
                "is_eol": product.is_eol,
            },
            "active_offer": (
                {
                    "id_supplier": active_offer.id_supplier,
                    "id_supplier_item": active_offer.id_supplier_item,
                    "unit_cost": active_offer.unit_cost,
                    "unit_price_sent": active_offer.unit_price_sent,
                    "stock_sent": active_offer.stock_sent,
                }
                if active_offer is not None
                else None
            ),
            "shipping": {"id_supplier": active_offer.id_supplier if active_offer else None},
        }

    def enqueue_product_state_change(
        self,
        *,
        product: Product,
        active_offer: ProductActiveOffer | None,
        reason: str,
        priority: int,
    ) -> CatalogUpdateStream:
        payload_dict = self._build_payload(product, active_offer, reason=reason)

        evt = CatalogUpdateStream(
            id_product=product.id,
            id_ecommerce=product.id_ecommerce,
            event_type="product_state_changed",
            priority=priority,
            status="pending",
            payload=json.dumps(payload_dict, ensure_ascii=False),
            available_at=datetime.utcnow(),
        )
        self.db.add(evt)
        # commit fica a cargo do chamador (uow)
        return evt

    def claim_pending_batch(
        self,
        *,
        limit: int = 50,
        min_priority: int | None = None,
    ) -> list[CatalogUpdateStream]:
        """
        Vai buscar um batch de eventos `pending` e marca-os como `processing`.
        Não fazemos SKIP LOCKED por agora – 1 consumidor chega e sobra.
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
            CatalogUpdateStream.created_at.asc(),
            CatalogUpdateStream.id.asc(),
        )

        events = q.limit(limit).all()

        for evt in events:
            evt.status = "processing"
            evt.attempts += 1

        # commit é responsabilidade do chamador (UoW)
        return events

    def ack_batch(
        self,
        *,
        ids: list[int],
        status: str,
        error: str | None = None,
    ) -> int:
        """
        Marca um conjunto de eventos como concluídos (done|failed).
        """
        now = datetime.utcnow()
        q = self.db.query(CatalogUpdateStream).filter(CatalogUpdateStream.id.in_(ids))

        count = 0
        for evt in q.all():
            evt.status = status
            evt.last_error = error
            evt.processed_at = now
            count += 1

        return count
