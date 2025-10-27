# app/models/product.py
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, Text, Numeric, Boolean, DateTime, Index, text
from app.infra.base import Base, utcnow

if TYPE_CHECKING:
    from .product_meta import ProductMeta
    from .product_supplier_event import ProductSupplierEvent

class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # gtin agora pode ser nulo
    gtin: Mapped[Optional[str]] = mapped_column(Text, nullable=True, index=True)

    id_ecommerce: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    id_brand: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    id_category: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    partnumber: Mapped[str | None] = mapped_column(Text, nullable=True)
    name: Mapped[str | None] = mapped_column(Text, nullable=True)
    margin: Mapped[float] = mapped_column(Numeric(7,4), nullable=False, default=0)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_eol: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    weight_str: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    meta: Mapped[list["ProductMeta"]] = relationship("ProductMeta", back_populates="product", cascade="all,delete-orphan")
    supplier_events: Mapped[list["ProductSupplierEvent"]] = relationship("ProductSupplierEvent", back_populates="product", cascade="all,delete-orphan")

    __table_args__ = (
        # UNIQUE (gtin) WHEN gtin IS NOT NULL
        Index("uq_products_gtin_not_null", "gtin", unique=True, postgresql_where=text("gtin IS NOT NULL")),
        # UNIQUE (id_brand, partnumber) WHEN both NOT NULL
        Index("uq_products_brand_mpn", "id_brand", "partnumber", unique=True,
              postgresql_where=text("id_brand IS NOT NULL AND partnumber IS NOT NULL")),
    )
