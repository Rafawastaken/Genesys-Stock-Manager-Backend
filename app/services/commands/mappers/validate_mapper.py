# app/services/commands/mappers/validate_mapper.py
from __future__ import annotations
import json
from typing import Optional, Dict, Any, List
from app.infra.uow import UoW
from app.schemas.mappers import MapperValidateIn, MapperValidateOut

def _validate(profile: Dict[str, Any] | None, headers: Optional[List[str]]) -> Dict[str, Any]:
    """
    Validação leve: verifica se 'fields' mapeia os essenciais (gtin, price, stock).
    Se headers forem fornecidos, confere se as 'source' existem nos headers.
    """
    profile = profile or {}
    fields = profile.get("fields") or {}
    required = {"gtin", "price", "stock"}

    # normaliza para dict {target: {source: "..."}} mesmo que viesse em lista.
    if isinstance(fields, list):
        norm = {}
        for row in fields:
            t = (row or {}).get("target")
            if t: norm[t] = {k: v for k, v in row.items() if k != "target"}
        fields = norm

    errors = []
    for r in required:
        if r not in fields:
            errors.append({"code": "missing_field", "msg": f"Campo requerido '{r}' não está mapeado"})

    headers_checked = False
    if headers is not None:
        headers_checked = True
        hdrset = {h.lower() for h in headers}
        for tgt, cfg in fields.items():
            src = (cfg or {}).get("source") or (cfg or {}).get("from")
            if src and src.lower() not in hdrset:
                errors.append({"code": "missing_source", "msg": f"Fonte '{src}' não existe nos headers"})

    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "warnings": [],
        "required_coverage": {r: (r in fields) for r in required},
        "headers_checked": headers_checked,
    }

def handle(uow: UoW, *, feed_id: int, payload: MapperValidateIn) -> MapperValidateOut:
    profile: Optional[Dict[str, Any]] = payload.profile
    if profile is None:
        e = uow.mappers.get_by_feed(feed_id)
        if not e or not e.profile_json:
            return MapperValidateOut(ok=False, errors=[{"code": "not_found", "msg": "Mapper não existe para este feed"}],
                                     warnings=[], required_coverage={}, headers_checked=False)
        try:
            profile = json.loads(e.profile_json)
        except Exception:
            profile = {}

    res = _validate(profile, headers=payload.headers)
    return MapperValidateOut(**res)
