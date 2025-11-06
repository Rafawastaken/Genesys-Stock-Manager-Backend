# app/domains/catalog/repos.py

from app.repositories.brand_repo import BrandRepository
from app.repositories.category_repo import CategoryRepository
from app.repositories.product_repo import ProductRepository

__all__ = [
    "BrandRepository",
    "CategoryRepository",
    "ProductRepository",
]
