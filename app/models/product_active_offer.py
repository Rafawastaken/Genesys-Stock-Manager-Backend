# app/models/product_active_offer.py
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infra.base import Base, utcnow

if TYPE_CHECKING:
    from .product import Product
    from .supplier import Supplier
    from .supplier_item import SupplierItem


class ProductActiveOffer(Base):
    """
    Oferta ativa por produto (o que o PrestaShop *deve* estar a usar neste momento).

    - Um registo por produto (UNIQUE id_product).
    - Guarda a referência ao supplier/supplier_item, custo, preço enviado e stock enviado.
    - Usada para:
        * saber qual fornecedor está “ativo”,
        * shipping quote,
        * debugging de sync com PrestaShop.
    """

    __tablename__ = "products_active_offers"
    __table_args__ = (
        UniqueConstraint("id_product", name="uq_pao_product"),
        Index("ix_pao_product_supplier", "id_product", "id_supplier"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    id_product: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # redundante mas útil para queries rápidas
    id_supplier: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("suppliers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    id_supplier_item: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("supplier_items.id", ondelete="SET NULL"),
        nullable=True,
    )

    # custo unitário da oferta (em moeda base, ex. EUR)
    unit_cost: Mapped[float | None] = mapped_column(
        Numeric(12, 4),
        nullable=True,
    )

    # preço de venda que foi comunicado ao PrestaShop
    unit_price_sent: Mapped[float | None] = mapped_column(
        Numeric(12, 4),
        nullable=True,
    )

    # stock que foi comunicado ao PrestaShop (para este produto)
    stock_sent: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # última vez que este registo foi sincronizado com o PrestaShop
    synced_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        default=utcnow,
    )

    # relacionamentos (apenas conveniência; não obrigatórios para funcionar)
    product: Mapped["Product"] = relationship(
        "Product",
        lazy="joined",
        back_populates="active_offer",
    )

    supplier: Mapped["Supplier | None"] = relationship("Supplier", lazy="joined")
    supplier_item: Mapped["SupplierItem | None"] = relationship("SupplierItem", lazy="joined")
