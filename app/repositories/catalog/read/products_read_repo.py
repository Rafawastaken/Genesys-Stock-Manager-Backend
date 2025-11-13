from __future__ import annotations

from sqlalchemy import select, func, and_, or_, exists
from sqlalchemy.orm import Session, aliased

from app.models.product import Product
from app.models.brand import Brand
from app.models.category import Category
from app.models.supplier_item import SupplierItem
from app.models.supplier_feed import SupplierFeed


class ProductsReadRepository:
    """
    Consultas de leitura para produtos (inclui joins/filtros com procurement
    apenas no caminho de leitura).
    """

    def __init__(self, db: Session):
        self.db = db

    # Lookups simples --------------------------------------------
    def get(self, id_product: int) -> Product | None:
        return self.db.get(Product, id_product)

    def get_by_gtin(self, gtin: str) -> Product | None:
        if not gtin:
            return None
        return self.db.scalar(select(Product).where(Product.gtin == gtin))

    def get_by_brand_mpn(self, id_brand: int, partnumber: str) -> Product | None:
        if not id_brand or not partnumber:
            return None
        stmt = select(Product).where(Product.id_brand == id_brand, Product.partnumber == partnumber)
        return self.db.scalar(stmt)

    # Lista paginada com filtros/sort ----------------------------
    def list_products(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        q: str | None = None,
        gtin: str | None = None,
        partnumber: str | None = None,
        id_brand: int | None = None,
        brand: str | None = None,
        id_category: int | None = None,
        category: str | None = None,
        has_stock: bool | None = None,
        id_supplier: int | None = None,
        sort: str = "recent",  # "recent" | "name" | "cheapest"
    ):
        page = max(1, page)
        page_size = max(1, min(page_size, 100))

        b = aliased(Brand)
        c = aliased(Category)
        si = aliased(SupplierItem)
        sf = aliased(SupplierFeed)

        base = (
            select(
                Product.id,
                Product.gtin,
                Product.id_ecommerce,
                Product.id_brand,
                Product.id_category,
                Product.partnumber,
                Product.name,
                Product.description,
                Product.image_url,
                Product.weight_str,
                Product.created_at,
                Product.updated_at,
                b.name.label("brand_name"),
                c.name.label("category_name"),
            )
            .select_from(Product)
            .join(b, b.id == Product.id_brand, isouter=True)
            .join(c, c.id == Product.id_category, isouter=True)
        )

        filters: list = []

        if q:
            like = f"%{q.strip()}%"
            filters.append(
                or_(
                    Product.name.ilike(like),
                    Product.partnumber.ilike(like),
                    Product.gtin.ilike(like),
                )
            )

        if gtin:
            filters.append(Product.gtin == gtin)

        if partnumber:
            filters.append(Product.partnumber == partnumber)

        if id_brand:
            filters.append(Product.id_brand == id_brand)
        elif brand:
            filters.append(
                func.lower(func.btrim(b.name))
                == func.lower(func.btrim(func.cast(brand, b.name.type)))
            )

        if id_category:
            filters.append(Product.id_category == id_category)
        elif category:
            filters.append(
                func.lower(func.btrim(c.name))
                == func.lower(func.btrim(func.cast(category, c.name.type)))
            )

        if has_stock is True:
            # existe pelo menos uma oferta com stock>0 para este produto
            exists_stock = exists(
                select(si.id).where(and_(si.id_product == Product.id, si.stock > 0))
            )
            filters.append(exists_stock)
        elif has_stock is False:
            # não existe nenhuma oferta com stock>0
            not_exists_stock = ~exists(
                select(si.id).where(and_(si.id_product == Product.id, si.stock > 0))
            )
            filters.append(not_exists_stock)

        if id_supplier:
            # existe pelo menos uma oferta deste supplier (com qualquer stock)
            exists_supplier_offer = exists(
                select(si.id)
                .join(sf, sf.id == si.id_feed)
                .where(and_(si.id_product == Product.id, sf.id_supplier == id_supplier))
            )
            filters.append(exists_supplier_offer)

        if filters:
            base = base.where(and_(*filters))

        # Ordenação
        if sort == "name":
            base = base.order_by(Product.name.asc().nulls_last(), Product.id.asc())
        elif sort == "cheapest":
            # menor preço entre ofertas com stock>0; NULLS LAST
            min_price_with_stock = (
                select(func.min(si.price))
                .select_from(si)
                .join(sf, sf.id == si.id_feed)
                .where(and_(si.id_product == Product.id, si.stock > 0, si.price.isnot(None)))
                .correlate(Product)
                .scalar_subquery()
            )
            base = base.order_by(
                min_price_with_stock.is_(None),
                min_price_with_stock.asc(),
                Product.id.asc(),
            )
        else:
            # recent: updated_at DESC, depois created_at DESC
            base = base.order_by(
                Product.updated_at.desc().nulls_last(),
                Product.created_at.desc(),
                Product.id.desc(),
            )

        total = self.db.scalar(select(func.count()).select_from(base.subquery())) or 0

        rows = self.db.execute(base.limit(page_size).offset((page - 1) * page_size)).all()

        return rows, int(total)
