# app/schemas/catalog_update_stream.py
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class CatalogUpdatePayload(BaseModel):
    reason: str
    product: dict[str, Any]
    active_offer: dict[str, Any] | None = None
    shipping: dict[str, Any] | None = None


class CatalogUpdateEventOut(BaseModel):
    id: int
    id_product: int
    id_ecommerce: int | None
    priority: int
    event_type: str
    created_at: datetime
    payload: CatalogUpdatePayload

    class Config:
        from_attributes = True


class CatalogUpdateBatchOut(BaseModel):
    items: list[CatalogUpdateEventOut]
    total: int


class CatalogUpdateAckIn(BaseModel):
    ids: list[int] = Field(..., min_length=1)
    status: Literal["done", "failed"]
    error: str | None = None
