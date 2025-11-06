# app/schemas/products.py
from datetime import datetime

from pydantic import BaseModel


class OfferOut(BaseModel):
    id_supplier: int
    supplier_name: str | None = None
    supplier_image: str | None = None
    id_feed: int
    sku: str
    price: str | None = None
    stock: int | None = None
    id_last_seen_run: int | None = None
    updated_at: datetime | None = None


class ProductOut(BaseModel):
    id: int
    gtin: str | None = None
    id_ecommerce: int | None = None
    id_brand: int | None = None
    brand_name: str | None = None
    id_category: int | None = None
    category_name: str | None = None
    partnumber: str | None = None
    name: str | None = None
    description: str | None = None
    image_url: str | None = None
    # category_path removido
    weight_str: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    offers: list[OfferOut] = []
    best_offer: OfferOut | None = None


class ProductListOut(BaseModel):
    items: list[ProductOut]
    total: int
    page: int
    page_size: int
