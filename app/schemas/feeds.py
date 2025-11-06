from datetime import datetime
from typing import Any

from pydantic import BaseModel


class SupplierFeedCreate(BaseModel):
    kind: str
    format: str
    url: str
    active: bool = True
    headers: dict[str, str] | None = None
    params: dict[str, str] | None = None
    auth_kind: str | None = None
    auth: dict[str, Any] | None = None
    extra: dict[str, Any] | None = None
    csv_delimiter: str | None = ","


class SupplierFeedUpdate(SupplierFeedCreate):
    pass


class SupplierFeedOut(BaseModel):
    id: int
    id_supplier: int
    kind: str
    format: str
    url: str
    active: bool
    headers_json: str | None
    params_json: str | None
    auth_kind: str | None
    auth_json: str | None
    extra_json: str | None
    csv_delimiter: str | None
    has_auth: bool
    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True


class FeedTestRequest(BaseModel):
    kind: str | None = None
    format: str
    url: str
    headers: dict[str, str] | None = None
    params: dict[str, str] | None = None
    auth_kind: str | None = None
    auth: dict[str, Any] | None = None
    extra: dict[str, Any] | None = None
    csv_delimiter: str | None = ","
    max_rows: int | None = 20


class FeedTestResponse(BaseModel):
    ok: bool
    status_code: int
    content_type: str | None
    bytes_read: int
    preview_type: str | None  # "json"|"csv"|None
    rows_preview: list[dict[str, Any]] | None
    error: str | None = None
