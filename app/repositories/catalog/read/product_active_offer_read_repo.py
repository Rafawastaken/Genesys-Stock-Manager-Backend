# app/repositories/catalog/read/product_active_offer_read_repo.py
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.product_active_offer import ProductActiveOffer


class ProductActiveOfferReadRepository:
    """
    Operações de leitura para a oferta ativa de um produto.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_by_product(self, id_product: int) -> ProductActiveOffer | None:
        if not id_product:
            return None
        stmt = select(ProductActiveOffer).where(ProductActiveOffer.id_product == id_product)
        return self.db.scalar(stmt)

    def get(self, id_offer: int) -> ProductActiveOffer | None:
        return self.db.get(ProductActiveOffer, id_offer)

    def list_for_products(self, ids: list[int]) -> dict[int, ProductActiveOffer]:
        """
        Devolve um mapa {id_product: ProductActiveOffer} para uma lista de produtos.
        Útil para listagens em batch.
        """
        if not ids:
            return {}
        stmt = select(ProductActiveOffer).where(ProductActiveOffer.id_product.in_(ids))
        rows = self.db.scalars(stmt).all()
        return {row.id_product: row for row in rows}
