# app/models/supplier_item.py
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, ForeignKey, DateTime, UniqueConstraint
from app.infra.base import Base, utcnow

class SupplierItem(Base):
    __tablename__ = "supplier_items"
    __table_args__ = (UniqueConstraint("id_feed", "sku", name="uq_supplier_item_feed_sku"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_feed: Mapped[int] = mapped_column(Integer, ForeignKey("supplier_feeds.id", ondelete="CASCADE"), index=True)
    id_product: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("products.id", ondelete="SET NULL"), index=True, nullable=True)

    sku:  Mapped[str] = mapped_column(String(200), index=True)
    gtin: Mapped[Optional[str]] = mapped_column(String(40), default=None)
    partnumber: Mapped[Optional[str]] = mapped_column(String(120), default=None)
    price: Mapped[str] = mapped_column(String(40))
    stock: Mapped[int] = mapped_column(Integer)

    fingerprint: Mapped[str] = mapped_column(String(64), index=True)
    id_feed_run: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("feed_runs.id", ondelete="SET NULL"), index=True)

    feed = relationship("SupplierFeed", back_populates="items")
    product = relationship("Product")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=True)
