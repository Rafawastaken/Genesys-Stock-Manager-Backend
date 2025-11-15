# app/schemas/products.py
from __future__ import annotations
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


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


# --------------------------


class ProductMetaOut(BaseModel):
    name: str
    value: str


class ProductEventOut(BaseModel):
    model_config = ConfigDict(extra="forbid")  # apanha campos errados cedo
    created_at: datetime  # <- CHAVE OFICIAL
    reason: str
    price: str | None = None
    stock: int | None = None
    id_supplier: int | None = None
    supplier_name: str | None = None
    id_feed_run: int | None = None


class SeriesPointOut(BaseModel):
    date: datetime  # dia (00:00) ou timestamp consolidado do dia
    price: str | None = None
    stock: int | None = None


class ProductStatsOut(BaseModel):
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    suppliers_count: int = 0
    offers_in_stock: int = 0
    last_change_at: datetime | None = None


class ProductDetailOut(BaseModel):
    product: ProductOut
    meta: list[ProductMetaOut] = Field(default_factory=list)
    offers: list[OfferOut] = Field(default_factory=list)
    best_offer: OfferOut | None = None
    stats: ProductStatsOut
    events: list[ProductEventOut] | None = None
    series_daily: list[SeriesPointOut] | None = None
