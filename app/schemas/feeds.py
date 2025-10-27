from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

class SupplierFeedCreate(BaseModel):
    kind: str
    format: str
    url: str
    active: bool = True
    headers: Optional[Dict[str,str]] = None
    params: Optional[Dict[str,str]] = None
    auth_kind: Optional[str] = None
    auth: Optional[Dict[str, Any]] = None
    extra: Optional[Dict[str, Any]] = None
    csv_delimiter: Optional[str] = ","

class SupplierFeedUpdate(SupplierFeedCreate):
    pass

class SupplierFeedOut(BaseModel):
    id: int
    id_supplier: int
    kind: str
    format: str
    url: str
    active: bool
    headers_json: Optional[str]
    params_json: Optional[str]
    auth_kind: Optional[str]
    auth_json: Optional[str]
    extra_json: Optional[str]
    csv_delimiter: Optional[str]
    has_auth: bool
    created_at: datetime
    updated_at: Optional[datetime]
    class Config: from_attributes = True

class FeedTestRequest(BaseModel):
    kind: Optional[str] = None
    format: str
    url: str
    headers: Optional[Dict[str,str]] = None
    params: Optional[Dict[str,str]] = None
    auth_kind: Optional[str] = None
    auth: Optional[Dict[str, Any]] = None
    extra: Optional[Dict[str, Any]] = None
    csv_delimiter: Optional[str] = ","
    max_rows: Optional[int] = 20

class FeedTestResponse(BaseModel):
    ok: bool
    status_code: int
    content_type: Optional[str]
    bytes_read: int
    preview_type: Optional[str]  # "json"|"csv"|None
    rows_preview: Optional[List[Dict[str, Any]]]
    error: Optional[str] = None
