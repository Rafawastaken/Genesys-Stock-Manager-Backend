from __future__ import annotations
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class OfferOut(BaseModel):
    id_supplier: int
    supplier_name: Optional[str] = None
    id_feed: int
    sku: str
    price: str
    stock: int
    id_last_seen_run: Optional[int] = None
    updated_at: Optional[datetime] = None

class ProductOut(BaseModel):
    id: int
    gtin: Optional[str] = None
    id_brand: Optional[int] = None
    brand_name: Optional[str] = None
    id_category: Optional[int] = None
    category_name: Optional[str] = None
    partnumber: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    category_path: Optional[str] = None
    weight_str: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    offers: List[OfferOut] = []
    best_offer: Optional[OfferOut] = None

class ProductListOut(BaseModel):
    items: List[ProductOut]
    total: int
    page: int
    page_size: int
