# Reexporta os repositórios atuais sob o namespace de domínio `procurement`.

from app.repositories.feed_run_repo import FeedRunRepository
from app.repositories.mapper_repo import MapperRepository
from app.repositories.product_event_repo import ProductEventRepository
from app.repositories.supplier_feed_repo import SupplierFeedRepository
from app.repositories.supplier_item_repo import SupplierItemRepository
from app.repositories.supplier_repo import SupplierRepository

__all__ = [
    "FeedRunRepository",
    "MapperRepository",
    "SupplierItemRepository",
    "SupplierFeedRepository",
    "SupplierRepository",
    "ProductEventRepository",
]
