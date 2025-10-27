# app/services/queries/feeds/get_by_supplier.py
from __future__ import annotations
import json
from app.infra.uow import UoW
from app.repositories.supplier_feed_repo import SupplierFeedRepository
from app.schemas.feeds import SupplierFeedOut

def _to_out(e) -> SupplierFeedOut:
    has_auth = False
    try:
        parsed = json.loads(e.auth_json) if e.auth_json else {}
        has_auth = bool(parsed)
    except Exception:
        has_auth = False
    return SupplierFeedOut(
        id=e.id,
        supplier_id=e.supplier_id,
        kind=e.kind,
        format=e.format,
        url=e.url,
        active=e.active,
        headers_json=e.headers_json,
        params_json=e.params_json,
        auth_kind=e.auth_kind,
        auth_json=e.auth_json,
        extra_json=e.extra_json,
        csv_delimiter=e.csv_delimiter or ",",
        has_auth=has_auth,
        created_at=e.created_at,
        updated_at=e.updated_at,
    )

def handle(uow: UoW, *, supplier_id: int):
    repo = SupplierFeedRepository(uow.db)
    e = repo.get_by_supplier(supplier_id)
    if not e:
        raise ValueError("FEED_NOT_FOUND")
    return e
