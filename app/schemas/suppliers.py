from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from app.schemas.feeds import SupplierFeedOut, SupplierFeedUpdate
from app.schemas.mappers import FeedMapperOut, FeedMapperUpsert


class SupplierCreate(BaseModel):
    name: str
    active: bool = True
    logo_image: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    margin: float = 0
    country: Optional[str] = None

class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    active: Optional[bool] = None
    logo_image: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    margin: Optional[float] = None
    country: Optional[str] = None

class SupplierOut(BaseModel):
    id: int
    name: str
    active: bool
    logo_image: Optional[str]
    contact_name: Optional[str]
    contact_phone: Optional[str]
    contact_email: Optional[str]
    margin: float
    country: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    class Config: from_attributes = True

class SupplierList(BaseModel):
    items: List[SupplierOut]
    total: int
    page: int
    page_size: int

class SupplierDetailOut(BaseModel):
    supplier: SupplierOut
    feed: Optional[SupplierFeedOut]
    mapper: Optional[FeedMapperOut]

class SupplierBundleUpdate(BaseModel):
    supplier: Optional[SupplierUpdate] = None
    feed: Optional[SupplierFeedUpdate] = None
    mapper: Optional[FeedMapperUpsert] = None