# app/domains/procurement/usecases/mappers/validate_mapper.py
# Validate mapping profiles for procurement feeds (no exceptions; returns a structured result).

from __future__ import annotations

import json
from typing import Any

from app.domains.procurement.repos import MapperRepository
from app.infra.uow import UoW
from app.schemas.mappers import MapperValidateIn, MapperValidateOut


def _validate(profile: dict[str, Any] | None, headers: list[str] | None) -> dict[str, Any]:
    """
    Light validation: ensure 'fields' maps required targets (gtin, price, stock).
    If headers are provided, verify each field's 'source' exists in headers.
    """
    profile = profile or {}
    fields = profile.get("fields") or {}
    required = {"gtin", "price", "stock"}

    # Normalize to dict {target: {source: "..."}}, even if it came as a list.
    if isinstance(fields, list):
        norm = {}
        for row in fields:
            t = (row or {}).get("target")
            if t:
                norm[t] = {k: v for k, v in row.items() if k != "target"}
        fields = norm

    errors = []
    for r in required:
        if r not in fields:
            errors.append({"code": "missing_field", "msg": f"Required field '{r}' is not mapped"})

    headers_checked = False
    if headers is not None:
        headers_checked = True
        hdrset = {str(h).lower() for h in headers}
        for _tgt, cfg in fields.items():  # rename tgt -> _tgt
            src = (cfg or {}).get("source") or (cfg or {}).get("from")
            if src and str(src).lower() not in hdrset:
                errors.append(
                    {"code": "missing_source", "msg": f"Source '{src}' does not exist in headers"}
                )

    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "warnings": [],
        "required_coverage": {r: (r in fields) for r in required},
        "headers_checked": headers_checked,
    }


def execute(uow: UoW, *, id_feed: int, payload: MapperValidateIn) -> MapperValidateOut:
    profile: dict[str, Any] | None = payload.profile

    if profile is None:
        # No payload profile → fetch from repository (no UoW aggregator).
        repo = MapperRepository(uow.db)
        e = repo.get_by_feed(id_feed)
        if not e or not getattr(e, "profile_json", None):
            return MapperValidateOut(
                ok=False,
                errors=[{"code": "not_found", "msg": "Mapper not found for this feed"}],
                warnings=[],
                required_coverage={},
                headers_checked=False,
            )
        try:
            profile = json.loads(e.profile_json)
        except Exception:
            profile = {}

    res = _validate(profile, headers=payload.headers)
    return MapperValidateOut(**res)
