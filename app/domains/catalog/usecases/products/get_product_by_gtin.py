# app/domains/catalog/usecases/products/get_product_by_gtin.py
from app.infra.uow import UoW
from app.core.errors import NotFound
from app.repositories.catalog.read.products_read_repo import ProductsReadRepository
from app.domains.catalog.read_services.product_detail import get_product_detail, DetailOptions
from app.schemas.products import ProductDetailOut


def execute(uow: UoW, *, gtin: str, **kwargs) -> ProductDetailOut:
    gtin = (gtin or "").strip()
    if not gtin:
        raise NotFound("GTIN inválido.")
    pid = ProductsReadRepository(uow.db).get_id_by_gtin(gtin)
    if not pid:
        raise NotFound(f"Product with GTIN {gtin} not found.")
    return get_product_detail(uow, id_product=pid, opts=DetailOptions(**kwargs))
