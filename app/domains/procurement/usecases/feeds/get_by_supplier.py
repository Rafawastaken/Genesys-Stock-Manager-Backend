from __future__ import annotations

import json

from app.core.errors import NotFound
from app.domains.procurement.repos import SupplierFeedRepository
from app.infra.uow import UoW
from app.schemas.feeds import SupplierFeedOut


def _to_out(e) -> SupplierFeedOut:
    has_auth = False
    try:
        parsed = json.loads(e.auth_json) if getattr(e, "auth_json", None) else {}
        has_auth = bool(parsed)
    except Exception:
        has_auth = False
    return SupplierFeedOut(
        id=e.id,
        id_supplier=e.id_supplier,
        kind=e.kind,
        format=e.format,
        url=e.url,
        active=e.active,
        headers_json=getattr(e, "headers_json", None),
        params_json=getattr(e, "params_json", None),
        auth_kind=getattr(e, "auth_kind", None),
        auth_json=getattr(e, "auth_json", None),
        extra_json=getattr(e, "extra_json", None),
        csv_delimiter=(getattr(e, "csv_delimiter", None) or ","),
        has_auth=has_auth,
        created_at=e.created_at,
        updated_at=e.updated_at,
    )


def execute(uow: UoW, *, id_supplier: int):
    repo = SupplierFeedRepository(uow.db)
    e = repo.get_by_supplier(id_supplier)
    if not e:
        raise NotFound("Feed not found")
    return e
