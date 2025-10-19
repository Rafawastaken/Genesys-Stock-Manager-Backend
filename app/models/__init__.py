# app/models/__init__.py
from app.infra.base import Base  # re-export
from .enums import FEED_KIND, FEED_FORMAT, RUN_STATUS
from .supplier import Supplier
from .supplier_feed import SupplierFeed
from .supplier_item import SupplierItem
from .feed_run import FeedRun
from .feed_mapper import FeedMapper
from .brand import Brand
from .category import Category
from .product import Product
from .product_meta import ProductMeta
from .product_supplier_event import ProductSupplierEvent

__all__ = [
    "Base","Brand","Category","FEED_KIND","FEED_FORMAT","RUN_STATUS","FeedMapper",
    "FeedRun","Product","ProductMeta","ProductSupplierEvent","Supplier","SupplierFeed","SupplierItem",
]

def create_db_and_tables(bind=None) -> None:
    """
    Cria todas as tabelas definidas pelos modelos.
    Se `bind` não for passado, usa o engine padrão.
    """
    if bind is None:
        from app.infra.session import engine as _engine
        bind = _engine
    Base.metadata.create_all(bind=bind)