from __future__ import annotations
from app.infra.uow import UoW

def execute(uow: UoW, *, id_supplier: int) -> None:
    """
    Delete the supplier's feed using the UoW aggregator, then commit.
    Mirrors the old command: uow.feeds.delete_by_supplier(id_supplier)
    """
    try:
        uow.feeds.delete_by_supplier(id_supplier)
        uow.commit()
    except Exception:
        uow.rollback()
        raise
