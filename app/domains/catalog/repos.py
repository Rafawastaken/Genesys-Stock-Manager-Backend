# app/domains/catalog/repos.py

from app.repositories.catalog.read.brand_read_repo import BrandsReadRepository
from app.repositories.catalog.write.brand_write_repo import BrandsWriteRepository
from app.repositories.catalog.read.category_read_repo import CategoryReadRepository
from app.repositories.catalog.write.category_write_repo import CategoryWriteRepository
from app.repositories.catalog.read.products_read_repo import ProductsReadRepository
from app.repositories.catalog.write.product_write_repo import ProductWriteRepository

__all__ = [
    "BrandsReadRepository",
    "BrandsWriteRepository",
    "CategoryReadRepository",
    "CategoryWriteRepository",
    "ProductsReadRepository",
    "ProductWriteRepository",
]
