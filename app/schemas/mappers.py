from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

class FeedMapperOut(BaseModel):
    id: int
    feed_id: int
    profile: Dict[str, Any]
    version: int
    created_at: datetime
    updated_at: Optional[datetime]
    class Config: from_attributes = True

class FeedMapperUpsert(BaseModel):
    profile: Dict[str, Any]
    bump_version: bool = True

class MapperValidateIn(BaseModel):
    profile: Optional[Dict[str, Any]] = None
    headers: Optional[List[str]] = None

class MapperValidateOut(BaseModel):
    ok: bool
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    required_coverage: Dict[str, Any]
    headers_checked: bool
