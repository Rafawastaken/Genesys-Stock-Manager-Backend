# app/repositories/catalog/write/product_active_offer_write_repo.py
from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infra.base import utcnow
from app.models.product_active_offer import ProductActiveOffer


class ProductActiveOfferWriteRepository:
    """
    Operações de escrita para oferta ativa.

    - upsert por id_product
    - usado pelos serviços que recalculam a best offer
    """

    def __init__(self, db: Session):
        self.db = db

    def get_by_product(self, id_product: int) -> ProductActiveOffer | None:
        if not id_product:
            return None
        stmt = select(ProductActiveOffer).where(ProductActiveOffer.id_product == id_product)
        return self.db.scalar(stmt)

    def upsert(
        self,
        *,
        id_product: int,
        id_supplier: int | None,
        id_supplier_item: int | None,
        unit_cost: float | None,
        unit_price_sent: float | None,
        stock_sent: int | None,
        synced_at: datetime | None = None,
    ) -> ProductActiveOffer:
        """
        Cria ou atualiza a oferta ativa para um produto.
        Não faz commit — fica ao cargo do UoW.
        """
        entity = self.get_by_product(id_product)

        now = synced_at or utcnow()

        if entity is None:
            entity = ProductActiveOffer(
                id_product=id_product,
                id_supplier=id_supplier,
                id_supplier_item=id_supplier_item,
                unit_cost=unit_cost,
                unit_price_sent=unit_price_sent,
                stock_sent=stock_sent,
                synced_at=now,
            )
            self.db.add(entity)
        else:
            entity.id_supplier = id_supplier
            entity.id_supplier_item = id_supplier_item
            entity.unit_cost = unit_cost
            entity.unit_price_sent = unit_price_sent
            entity.stock_sent = stock_sent
            entity.synced_at = now

        self.db.flush()
        return entity
