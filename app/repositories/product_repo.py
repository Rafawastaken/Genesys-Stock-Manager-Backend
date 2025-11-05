# app/repositories/product_repo.py

from __future__ import annotations
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.product import Product
from app.models.product_meta import ProductMeta
from app.domains.catalog.repos import BrandRepository, CategoryRepository

class ProductRepository:
    def __init__(self, db: Session):
        self.db = db

    # --- match/criação ---
    def get_by_gtin(self, gtin: str) -> Optional[Product]:
        if not gtin:
            return None
        return self.db.scalar(select(Product).where(Product.gtin == gtin))

    def get_by_brand_mpn(self, id_brand: int, partnumber: str) -> Optional[Product]:
        if not id_brand or not partnumber:
            return None
        stmt = select(Product).where(Product.id_brand == id_brand, Product.partnumber == partnumber)
        return self.db.scalar(stmt)

    def get_or_create(self, *, gtin: Optional[str], partnumber: Optional[str], brand_name: Optional[str]) -> Product:
        # 1) GTIN ganha sempre
        if gtin:
            p = self.get_by_gtin(gtin)
            if p:
                return p

        # 2) Brand + MPN
        id_brand = None
        if brand_name:
            b_repo = BrandRepository(self.db)
            brand = b_repo.get_or_create(brand_name)
            id_brand = brand.id

        if id_brand and partnumber:
            p = self.get_by_brand_mpn(id_brand, partnumber)
            if p:
                return p

        # 3) Criar novo se houver pelo menos uma chave
        if not gtin and not (id_brand and partnumber):
            raise ValueError("no product key (gtin or brand+mpn)")

        p = Product(gtin=gtin, id_brand=id_brand, partnumber=partnumber)
        self.db.add(p)
        self.db.flush()
        return p

    # --- preencher canonicals se vazias ---
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

    # --- brand/category se vazios ---
    def fill_brand_category_if_empty(self, id_product: int, *, brand_name: Optional[str], category_name: Optional[str]):
        p = self.db.get(Product, id_product)
        if not p:
            return
        changed = False

        if brand_name and not p.id_brand:
            b = BrandRepository(self.db).get_or_create(brand_name)
            p.id_brand = b.id
            changed = True

        if category_name and not p.id_category:
            c = CategoryRepository(self.db).get_or_create(category_name)
            p.id_category = c.id
            changed = True

        if changed:
            self.db.add(p)
            self.db.flush()

    # --- meta (sem tocar em valores existentes) ---
    def add_meta_if_missing(self, id_product: int, *, name: str, value: str) -> tuple[bool, bool]:
        stmt = select(ProductMeta).where(ProductMeta.id_product == id_product, ProductMeta.name == name)
        row = self.db.scalar(stmt)
        if row is None:
            self.db.add(ProductMeta(id_product=id_product, name=name, value=value))
            return True, False
        else:
            return (False, (row.value or "") != (value or ""))
