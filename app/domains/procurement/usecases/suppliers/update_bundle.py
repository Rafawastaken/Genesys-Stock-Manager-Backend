from __future__ import annotations
import json
from fastapi import HTTPException
from app.infra.uow import UoW

from app.domains.procurement.repos import (
    SupplierFeedRepository,
    SupplierRepository,
    MapperRepository,
)

from app.schemas.suppliers import SupplierBundleUpdate, SupplierDetailOut
from app.services.queries.suppliers import get_supplier_detail as q_detail


def execute(uow: UoW, *, id_supplier: int, payload: SupplierBundleUpdate) -> SupplierDetailOut:
    sup_repo = SupplierRepository(uow.db)
    feed_repo = SupplierFeedRepository(uow.db)
    map_repo  = MapperRepository(uow.db)

    # 1) Supplier
    if payload.supplier is not None:
        s = sup_repo.get(id_supplier)
        if not s:
            # manter mensagens em inglês como pediste
            raise HTTPException(status_code=404, detail="Supplier not found")

        data = payload.supplier
        for f in ("name", "active", "logo_image", "contact_name", "contact_phone", "contact_email", "margin", "country"):
            v = getattr(data, f, None)
            if v is not None:
                setattr(s, f, v)

    # 2) Feed (upsert por supplier)
    feed_entity = None
    if payload.feed is not None:
        def mutate(e):
            # base
            for f in ("kind", "format", "url", "active", "csv_delimiter", "auth_kind"):
                v = getattr(payload.feed, f, None)
                if v is not None:
                    setattr(e, f, v)
            # json blobs
            if payload.feed.headers is not None:
                e.headers_json = json.dumps(payload.feed.headers, ensure_ascii=False)
            if payload.feed.params is not None:
                e.params_json = json.dumps(payload.feed.params, ensure_ascii=False)
            if payload.feed.extra is not None:
                e.extra_json = json.dumps(payload.feed.extra, ensure_ascii=False)
            if payload.feed.auth is not None:
                e.auth_json = json.dumps(payload.feed.auth, ensure_ascii=False)

        feed_entity = feed_repo.upsert_for_supplier(id_supplier, mutate)

    # 3) Mapper (precisa saber o id_feed)
    if payload.mapper is not None:
        # se não atualizámos feed agora, tenta obter o existente
        if feed_entity is None:
            feed_entity = feed_repo.get_by_supplier(id_supplier)
        if not feed_entity:
            raise HTTPException(status_code=400, detail="Cannot upsert mapper without a feed for this supplier")

        # suportar ambos os nomes de campo possíveis: id vs id_feed
        feed_id = getattr(feed_entity, "id", None)
        if feed_id is None:
            feed_id = getattr(feed_entity, "id_feed", None)
        if feed_id is None:
            raise HTTPException(status_code=500, detail="Feed entity missing id")

        map_repo.upsert_profile(
            feed_id,
            payload.mapper.profile or {},
            bump_version=payload.mapper.bump_version,
        )

    # Commit no fim para tudo ser transacional
    uow.commit()

    # Reutiliza a query de detalhe para devolver o estado atual
    return q_detail.handle(uow, id_supplier=id_supplier)
