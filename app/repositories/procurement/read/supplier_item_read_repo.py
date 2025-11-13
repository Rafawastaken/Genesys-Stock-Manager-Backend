from __future__ import annotations
from typing import Any
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.supplier_item import SupplierItem as SI
from app.models.supplier_feed import SupplierFeed as SF
from app.models.supplier import Supplier as S


class SupplierItemReadRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_offers_for_product_ids(
        self,
        product_ids: Sequence[int],
        only_in_stock: bool = False,
    ) -> list[dict[str, Any]]:
        """
        Devolve as ofertas (SupplierItem) para uma lista de products,
        já com join ao SupplierFeed/Supplier para nome/logo do fornecedor.
        """
        if not product_ids:
            return []

        q = (
            select(
                SI.id_product.label("id_product"),
                SI.id_feed.label("id_feed"),
                SF.id_supplier.label("id_supplier"),
                S.name.label("supplier_name"),
                S.logo_image.label("supplier_image"),
                SI.sku.label("sku"),
                SI.price.label("price"),
                SI.stock.label("stock"),
                SI.id_feed_run.label("id_last_seen_run"),
                SI.updated_at.label("updated_at"),
            )
            .join(SF, SF.id == SI.id_feed)
            .join(S, S.id == SF.id_supplier)
            .where(SI.id_product.in_(list(product_ids)))
        )

        if only_in_stock:
            q = q.where(SI.stock > 0)

        return [dict(r._mapping) for r in self.db.execute(q).all()]

    def list_offers_for_product(
        self, id_product: int, *, only_in_stock: bool = False
    ) -> list[dict[str, Any]]:
        q = (
            select(
                SI.id_product.label("id_product"),
                SI.id_feed.label("id_feed"),
                SF.id_supplier.label("id_supplier"),
                S.name.label("supplier_name"),
                S.logo_image.label("supplier_image"),
                SI.sku.label("sku"),
                SI.price.label("price"),
                SI.stock.label("stock"),
                SI.id_feed_run.label("id_last_seen_run"),
                SI.updated_at.label("updated_at"),
            )
            .join(SF, SF.id == SI.id_feed)
            .join(S, S.id == SF.id_supplier)
            .where(SI.id_product == id_product)
        )
        if only_in_stock:
            q = q.where(SI.stock > 0)
        return [dict(r._mapping) for r in self.db.execute(q).all()]
