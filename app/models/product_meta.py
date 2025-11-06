# app/models/product_meta.py
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infra.base import Base, utcnow

if TYPE_CHECKING:
    from app.models.product import Product


class ProductMeta(Base):
    __tablename__ = "product_meta"
    __table_args__ = (
        # um nome de meta único por produto
        UniqueConstraint("id_product", "name", name="uq_product_meta_name_cs"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_product: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)  # e.g., "color", "size", "warranty"
    value: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow, nullable=True
    )

    product: Mapped["Product"] = relationship("Product", back_populates="meta")
