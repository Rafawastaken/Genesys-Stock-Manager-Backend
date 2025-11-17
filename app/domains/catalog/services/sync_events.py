# app/domains/catalog/services/sync_events.py
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.product_active_offer import ProductActiveOffer
from app.repositories.catalog.write.catalog_update_stream_write_repo import (
    CatalogUpdateStreamWriteRepository,
)


def compute_priority(
    *,
    prev_stock: int | None,
    new_stock: int | None,
) -> int:
    prev = prev_stock or 0
    new = new_stock or 0

    if prev > 0 and new == 0:
        return 10  # crítico: ficou esgotado
    if prev == 0 and new > 0:
        return 8  # importante: voltou a ter stock
    return 5  # default


def emit_product_state_event(
    db: Session,
    *,
    product: Product,
    active_offer: ProductActiveOffer | None,
    reason: str,
    prev_stock: int | None,
) -> None:
    repo = CatalogUpdateStreamWriteRepository(db)
    new_stock = active_offer.stock_sent if active_offer else 0
    priority = compute_priority(prev_stock=prev_stock, new_stock=new_stock)
    repo.enqueue_product_state_change(
        product=product,
        active_offer=active_offer,
        reason=reason,
        priority=priority,
    )
