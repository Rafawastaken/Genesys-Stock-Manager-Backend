# app/schemas/products.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class OfferOut(BaseModel):
    id_supplier: int
    supplier_name: Optional[str] = None
    supplier_image: Optional[str] = None
    id_feed: int
    sku: str
    price: Optional[str] = None
    stock: Optional[int] = None
    id_last_seen_run: Optional[int] = None
    updated_at: Optional[datetime] = None

class ProductOut(BaseModel):
    id: int
    gtin: Optional[str] = None
    id_ecommerce: Optional[int] = None
    id_brand: Optional[int] = None
    brand_name: Optional[str] = None
    id_category: Optional[int] = None
    category_name: Optional[str] = None
    partnumber: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    # category_path removido
    weight_str: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    offers: List[OfferOut] = []
    best_offer: Optional[OfferOut] = None

class ProductListOut(BaseModel):
    items: List[ProductOut]
    total: int
    page: int
    page_size: int
