# app/repositories/catalog/write/catalog_update_stream_write_repo.py

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.product_active_offer import ProductActiveOffer


class CatalogUpdateStreamWriteRepo:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _build_payload(
        self, product: Product, active_offer: ProductActiveOffer | None, reason: str
    ) -> dict[str, Any]:
        """
        Snapshot minimal para o modulo de Prestashop aplicar:
        - dados de produto
        - dados de oferta ativa
        - hint para shipping
        """
        return {"reason": reason, "product": {"id_product": product.id}}
