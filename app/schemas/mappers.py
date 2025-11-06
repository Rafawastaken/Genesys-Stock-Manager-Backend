from datetime import datetime
from typing import Any

from pydantic import BaseModel


class FeedMapperOut(BaseModel):
    id: int
    id_feed: int
    profile: dict[str, Any]
    version: int
    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True


class FeedMapperUpsert(BaseModel):
    profile: dict[str, Any]
    bump_version: bool = True


class MapperValidateIn(BaseModel):
    profile: dict[str, Any] | None = None
    headers: list[str] | None = None


class MapperValidateOut(BaseModel):
    ok: bool
    errors: list[dict[str, Any]]
    warnings: list[dict[str, Any]]
    required_coverage: dict[str, Any]
    headers_checked: bool
