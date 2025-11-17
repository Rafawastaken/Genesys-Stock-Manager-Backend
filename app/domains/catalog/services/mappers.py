from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.schemas.products import ProductOut, ProductListItemOut, OfferOut


def map_product_row_to_out(row: Any) -> ProductOut:
    """
    Converte um row vindo dos READ repos (SQLAlchemy row/ORM) num ProductOut base.

    Usamos getattr com default=None para ser tolerante a diferenças entre
    queries (ex.: list vs detail).
    """
    return ProductOut(
        id=row.id,
        gtin=getattr(row, "gtin", None),
        id_ecommerce=getattr(row, "id_ecommerce", None),
        id_brand=getattr(row, "id_brand", None),
        brand_name=getattr(row, "brand_name", None),
        id_category=getattr(row, "id_category", None),
        category_name=getattr(row, "category_name", None),
        partnumber=getattr(row, "partnumber", None),
        name=getattr(row, "name", None),
        margin=getattr(row, "margin", None),
        description=getattr(row, "description", None),
        image_url=getattr(row, "image_url", None),
        weight_str=getattr(row, "weight_str", None),
        created_at=getattr(row, "created_at", None),
        updated_at=getattr(row, "updated_at", None),
    )


def map_product_row_to_list_item(row: Any) -> ProductListItemOut:
    """
    Versão para listagens: parte do ProductOut base e embrulha num ProductListItemOut.
    """
    base = map_product_row_to_out(row)
    # model_dump garante que se no futuro adicionares campos, isto continua consistente
    return ProductListItemOut(**base.model_dump())


def map_offer_row_to_out(src: Mapping[str, Any]) -> OfferOut:
    """
    Converte o dict/row devolvido pelos SupplierItem READ repos num OfferOut.
    """
    return OfferOut(
        id_supplier=src["id_supplier"],
        supplier_name=src.get("supplier_name"),
        supplier_image=src.get("supplier_image"),
        id_feed=src["id_feed"],
        sku=src["sku"],
        price=src.get("price"),
        stock=src.get("stock"),
        id_last_seen_run=src.get("id_last_seen_run"),
        updated_at=src.get("updated_at"),
    )
