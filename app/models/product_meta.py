# app/models/product_meta.py
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, Text, DateTime, ForeignKey, UniqueConstraint
from app.infra.base import Base, utcnow

class ProductMeta(Base):
    __tablename__ = "product_meta"
    __table_args__ = (UniqueConstraint("id_product","name", name="uq_product_meta_name_cs"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_product: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    product: Mapped["Product"] = relationship("Product", back_populates="meta")