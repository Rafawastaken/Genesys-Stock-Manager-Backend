# app/repositories/product_repo.py
# Repository for Product model

from typing import Optional
from sqlalchemy import select, update, func, literal
from sqlalchemy.orm import Session
from .base import Repository
from app.models.product import Product

class ProductRepository(Repository[Product]):
    def __init__(self, db: Session): super().__init__(db, Product)

    def get_by_gtin(self, gtin: str) -> Optional[Product]:
        return self.db.scalar(select(Product).where(Product.gtin==gtin))

    def get_or_create_by_gtin(self, gtin: str) -> Product:
        p = self.get_by_gtin(gtin)
        if p: return p
        p = Product(gtin=gtin)
        self.db.add(p); self.db.flush()
        return p

    def fill_canonicals_if_empty(self, product_id: int, **vals) -> Product:
        stmt = (update(Product).where(Product.id==product_id).values(
            name=func.coalesce(Product.name, literal(vals.get("name"))),
            id_brand=func.coalesce(Product.id_brand, literal(vals.get("id_brand"))),
            id_category=func.coalesce(Product.id_category, literal(vals.get("id_category"))),
            description_html=func.coalesce(Product.description_html, literal(vals.get("description_html"))),
            image_url=func.coalesce(Product.image_url, literal(vals.get("image_url"))),
            category_path=func.coalesce(Product.category_path, literal(vals.get("category_path"))),
            weight_str=func.coalesce(Product.weight_str, literal(vals.get("weight_str"))),
            partnumber=func.coalesce(Product.partnumber, literal(vals.get("partnumber"))),
            updated_at=func.now(),
        ).returning(Product))
        return self.db.execute(stmt).scalar_one()
