# app/services/queries/suppliers/get_supplier_detail.py
from __future__ import annotations
import json
from typing import Optional, Dict, Any
from fastapi import HTTPException

from app.infra.uow import UoW
from app.repositories.supplier_repo import SupplierRepository
from app.repositories.supplier_feed_repo import SupplierFeedRepository
from app.repositories.mapper_repo import MapperRepository
from app.schemas.suppliers import SupplierDetailOut, SupplierOut
from app.schemas.feeds import SupplierFeedOut
from app.schemas.mappers import FeedMapperOut

def _supplier_to_out(s) -> SupplierOut:
    return SupplierOut(
        id=s.id,
        name=s.name,
        active=s.active,
        logo_image=s.logo_image,
        contact_name=s.contact_name,
        contact_phone=s.contact_phone,
        contact_email=s.contact_email,
        margin=s.margin,
        country=s.country,
        created_at=s.created_at,
        updated_at=s.updated_at,
    )

def _feed_to_out(f) -> SupplierFeedOut | None:
    if not f:
        return None
    # se o SupplierFeedOut exige *_json + has_auth, envia raw + flag
    return SupplierFeedOut.model_validate({
        "id": f.id,
        "supplier_id": f.supplier_id,
        "kind": f.kind,
        "format": f.format,
        "url": f.url,
        "active": f.active,
        "csv_delimiter": f.csv_delimiter,
        "headers_json": getattr(f, "headers_json", None),
        "params_json": getattr(f, "params_json", None),
        "extra_json": getattr(f, "extra_json", None),
        "auth_kind": getattr(f, "auth_kind", None),
        "auth_json": getattr(f, "auth_json", None),
        "has_auth": bool(getattr(f, "auth_json", None)),
        "created_at": f.created_at,
        "updated_at": f.updated_at,
    })

def _mapper_to_out(m) -> FeedMapperOut | None:
    if not m:
        return None
    return FeedMapperOut(
        id=m.id,
        feed_id=m.feed_id,
        profile=json.loads(m.profile_json) if getattr(m, "profile_json", None) else {},
        version=m.version or 1,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )

def handle(uow: UoW, *, supplier_id: int) -> SupplierDetailOut:
    sup_repo = SupplierRepository(uow.db)
    feed_repo = SupplierFeedRepository(uow.db)
    map_repo  = MapperRepository(uow.db)

    s = sup_repo.get(supplier_id)
    if not s:
        raise HTTPException(status_code=404, detail="Supplier not found")

    f = feed_repo.get_by_supplier(supplier_id)
    m = map_repo.get_by_feed(f.id) if f else None

    return SupplierDetailOut(
        supplier=_supplier_to_out(s),
        feed=_feed_to_out(f),
        mapper=_mapper_to_out(m),
    )
