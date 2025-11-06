# app/repositories/product_repo.py
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import InvalidArgument
from app.domains.catalog.repos import BrandRepository, CategoryRepository
from app.models.product import Product
from app.models.product_meta import ProductMeta


class ProductRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, id_product: int) -> Product | None:
        return self.db.get(Product, id_product)

    def get_by_gtin(self, gtin: str) -> Product | None:
        if not gtin:
            return None
        return self.db.scalar(select(Product).where(Product.gtin == gtin))

    def get_by_brand_mpn(self, id_brand: int, partnumber: str) -> Product | None:
        if not id_brand or not partnumber:
            return None
        stmt = select(Product).where(Product.id_brand == id_brand, Product.partnumber == partnumber)
        return self.db.scalar(stmt)

    def get_or_create(
        self, *, gtin: str | None, partnumber: str | None, brand_name: str | None
    ) -> Product:
        if gtin:
            p = self.get_by_gtin(gtin)
            if p:
                return p

        id_brand = None
        if brand_name:
            b_repo = BrandRepository(self.db)
            id_brand = b_repo.get_or_create(brand_name).id

        if id_brand and partnumber:
            p = self.get_by_brand_mpn(id_brand, partnumber)
            if p:
                return p

        if not gtin and not (id_brand and partnumber):
            raise InvalidArgument("Missing product key (gtin or brand+mpn)")

        p = Product(gtin=gtin, id_brand=id_brand, partnumber=partnumber)
        self.db.add(p)
        self.db.flush()
        return p

    def fill_canonicals_if_empty(self, id_product: int, **fields):
        p = self.db.get(Product, id_product)
        if not p:
            return
        changed = False
        for k, v in fields.items():
            if v in (None, ""):
                continue
            if getattr(p, k, None) in (None, "", 0):
                setattr(p, k, v)
                changed = True
        if changed:
            self.db.add(p)
            self.db.flush()

    def fill_brand_category_if_empty(
        self, id_product: int, *, brand_name: str | None, category_name: str | None
    ):
        p = self.db.get(Product, id_product)
        if not p:
            return
        changed = False
        if brand_name and not p.id_brand:
            p.id_brand = BrandRepository(self.db).get_or_create(brand_name).id
            changed = True
        if category_name and not p.id_category:
            p.id_category = CategoryRepository(self.db).get_or_create(category_name).id
            changed = True
        if changed:
            self.db.add(p)
            self.db.flush()

    def add_meta_if_missing(self, id_product: int, *, name: str, value: str) -> tuple[bool, bool]:
        row = self.db.scalar(
            select(ProductMeta).where(
                ProductMeta.id_product == id_product, ProductMeta.name == name
            )
        )
        if row is None:
            self.db.add(ProductMeta(id_product=id_product, name=name, value=value))
            # flush opcional se precisares do id
            return True, False
        else:
            return (False, (row.value or "") != (value or ""))
