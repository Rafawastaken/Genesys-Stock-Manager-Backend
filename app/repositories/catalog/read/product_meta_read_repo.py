from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.product_meta import ProductMeta


class ProductMetaReadRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_for_product(self, id_product: int) -> list[ProductMeta]:
        stmt = select(ProductMeta).where(ProductMeta.id_product == id_product)
        return self.db.execute(stmt).scalars().all()
