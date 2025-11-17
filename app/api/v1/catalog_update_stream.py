from __future__ import annotations


from fastapi import APIRouter, Depends, Query

from app.infra.uow import UoW
from app.core.deps import get_uow, require_access_token
from app.schemas.catalog_update_stream import (
    CatalogUpdateBatchOut,
    CatalogUpdateAckIn,
)

from app.domains.catalog.usecases.catalog_update_stream.get_pending_events import (
    execute as uc_get_pending,
)
from app.domains.catalog.usecases.catalog_update_stream.ack_events import (
    execute as uc_ack_events,
)


router = APIRouter(
    prefix="/catalog/update-stream",
    tags=["catalog-update-stream"],
    dependencies=[Depends(require_access_token)],
)


@router.get("/pending", response_model=CatalogUpdateBatchOut)
def get_pending_events(
    limit: int = Query(50, ge=1, le=500),
    min_priority: int | None = Query(None, ge=1),
    uow: UoW = Depends(get_uow),
) -> CatalogUpdateBatchOut:
    """
    Devolve um batch de eventos `pending` e marca-os como `processing`.
    A lógica de negócio vive no usecase.
    """
    result = uc_get_pending(
        uow,
        limit=limit,
        min_priority=min_priority,
    )

    return CatalogUpdateBatchOut(
        items=result,
        total=len(result),
    )


@router.post("/ack")
def ack_events(
    payload: CatalogUpdateAckIn,
    uow: UoW = Depends(get_uow),
) -> dict:
    """
    ACK de eventos (done | failed).
    Router só encaminha para o usecase.
    """
    return uc_ack_events(
        uow,
        ids=payload.ids,
        status=payload.status,
        error=payload.error,
    )
