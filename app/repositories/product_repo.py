# app/repositories/product_repo.py (partes novas/alteradas)
from __future__ import annotations
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.product import Product
from app.models.product_meta import ProductMeta
from app.repositories.brand_repo import BrandRepository
from app.repositories.category_repo import CategoryRepository

class ProductRepository:
    def __init__(self, db: Session):
        self.db = db

    # --- match/criação ---
    def get_by_gtin(self, gtin: str) -> Optional[Product]:
        if not gtin:
            return None
        return self.db.scalar(select(Product).where(Product.gtin == gtin))

    def get_by_brand_mpn(self, brand_id: int, partnumber: str) -> Optional[Product]:
        if not brand_id or not partnumber:
            return None
        stmt = select(Product).where(Product.id_brand == brand_id, Product.partnumber == partnumber)
        return self.db.scalar(stmt)

    def get_or_create(self, *, gtin: Optional[str], partnumber: Optional[str], brand_name: Optional[str]) -> Product:
        # 1) GTIN ganha sempre
        if gtin:
            p = self.get_by_gtin(gtin)
            if p:
                return p

        # 2) Brand + MPN
        brand_id = None
        if brand_name:
            b_repo = BrandRepository(self.db)
            brand = b_repo.get_or_create(brand_name)
            brand_id = brand.id

        if brand_id and partnumber:
            p = self.get_by_brand_mpn(brand_id, partnumber)
            if p:
                return p

        # 3) Criar novo se houver pelo menos uma chave
        if not gtin and not (brand_id and partnumber):
            raise ValueError("no product key (gtin or brand+mpn)")

        p = Product(gtin=gtin, id_brand=brand_id, partnumber=partnumber)
        self.db.add(p)
        self.db.flush()
        return p

    # --- preencher canonicals se vazias ---
    def fill_canonicals_if_empty(self, product_id: int, **fields):
        p = self.db.get(Product, product_id)
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
    def fill_brand_category_if_empty(self, product_id: int, *, brand_name: Optional[str], category_name: Optional[str]):
        p = self.db.get(Product, product_id)
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
    def add_meta_if_missing(self, product_id: int, *, name: str, value: str) -> tuple[bool, bool]:
        stmt = select(ProductMeta).where(ProductMeta.id_product == product_id, ProductMeta.name == name)
        row = self.db.scalar(stmt)
        if row is None:
            self.db.add(ProductMeta(id_product=product_id, name=name, value=value))
            return True, False
        else:
            return (False, (row.value or "") != (value or ""))
