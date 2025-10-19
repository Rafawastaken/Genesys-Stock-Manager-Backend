# app/services/commands/feeds/upsert_supplier_feed.py
from __future__ import annotations
import json
from app.infra.uow import UoW
from app.schemas.feeds import SupplierFeedCreate, SupplierFeedUpdate, SupplierFeedOut

def handle(uow: UoW, *, supplier_id: int, data: SupplierFeedCreate | SupplierFeedUpdate) -> SupplierFeedOut:
    def mutate(e):
        for f in ("kind", "format", "url", "active", "csv_delimiter"):
            v = getattr(data, f, None)
            if v is not None:
                setattr(e, f, v)
        # JSON limpos
        if getattr(data, "headers", None) is not None:
            e.headers_json = None if data.headers is None else json.dumps(data.headers, ensure_ascii=False)
        if getattr(data, "params", None) is not None:
            e.params_json = None if data.params is None else json.dumps(data.params, ensure_ascii=False)
        if getattr(data, "extra", None) is not None:
            e.extra_json = None if data.extra is None else json.dumps(data.extra, ensure_ascii=False)
        if getattr(data, "auth_kind", None) is not None:
            e.auth_kind = data.auth_kind or None
        if getattr(data, "auth", None) is not None:
            e.auth_json = None if data.auth is None else json.dumps(data.auth, ensure_ascii=False)

    e = uow.feeds.upsert_for_supplier(supplier_id, mutate)
    from app.services.queries.feeds.get_by_supplier import _to_out
    return _to_out(e)
