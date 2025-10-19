# app/services/commands/feeds/delete_supplier_feed.py
from __future__ import annotations
from app.infra.uow import UoW

def handle(uow: UoW, *, supplier_id: int) -> None:
    uow.feeds.delete_by_supplier(supplier_id)
