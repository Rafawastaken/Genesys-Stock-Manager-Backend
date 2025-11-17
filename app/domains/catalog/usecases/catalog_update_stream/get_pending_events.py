# app/domains/catalog/usecases/catalog_update_stream/get_pending_events.py
from __future__ import annotations

import json

from app.infra.uow import UoW
from app.repositories.catalog.write.catalog_update_stream_write_repo import (
    CatalogUpdateStreamWriteRepository,
)
from app.schemas.catalog_update_stream import (
    CatalogUpdateEventOut,
    CatalogUpdatePayload,
)


def execute(
    uow: UoW,
    *,
    limit: int,
    min_priority: int | None,
) -> list[CatalogUpdateEventOut]:
    """
    Usecase:
    - vai buscar um batch de eventos `pending`
    - marca-os como `processing`
    - devolve lista de CatalogUpdateEventOut
    """
    repo = CatalogUpdateStreamWriteRepository(uow.db)
    events = repo.claim_pending_batch(limit=limit, min_priority=min_priority)

    items_out: list[CatalogUpdateEventOut] = []

    for evt in events:
        payload_dict: dict[str, object] = {}
        if evt.payload:
            try:
                payload_dict = json.loads(evt.payload)
            except Exception:
                payload_dict = {}

        items_out.append(
            CatalogUpdateEventOut(
                id=evt.id,
                id_product=evt.id_product,
                id_ecommerce=evt.id_ecommerce,
                priority=evt.priority,
                event_type=evt.event_type,
                created_at=evt.created_at,
                payload=CatalogUpdatePayload.model_validate(payload_dict or {}),
            )
        )

    # já marcámos como processing lá no repo → commit aqui
    uow.commit()

    return items_out
