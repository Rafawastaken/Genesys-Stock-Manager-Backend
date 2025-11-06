# app/models/supplier_feed.py
# SQLAlchemy model for SupplierFeed

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infra.base import Base, utcnow

if TYPE_CHECKING:
    from app.models.feed_mapper import FeedMapper
    from app.models.feed_run import FeedRun
    from app.models.supplier import Supplier
    from app.models.supplier_item import SupplierItem


class SupplierFeed(Base):
    __tablename__ = "supplier_feeds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_supplier: Mapped[int] = mapped_column(
        ForeignKey("suppliers.id", ondelete="CASCADE"), unique=True, index=True
    )

    kind: Mapped[str] = mapped_column(String(10))
    format: Mapped[str] = mapped_column(String(10))
    url: Mapped[str] = mapped_column(String(1000))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    headers_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    params_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    auth_kind: Mapped[str | None] = mapped_column(String(30), nullable=True)
    auth_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    extra_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    csv_delimiter: Mapped[str | None] = mapped_column(String(4), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime, onupdate=utcnow, default=utcnow, nullable=True
    )

    supplier: Mapped["Supplier"] = relationship("Supplier", back_populates="feeds")
    runs: Mapped[list["FeedRun"]] = relationship(
        "FeedRun", back_populates="feed", cascade="all,delete-orphan"
    )
    items: Mapped[list["SupplierItem"]] = relationship(
        "SupplierItem", back_populates="feed", cascade="all,delete-orphan"
    )
    mapper: Mapped[Optional["FeedMapper"]] = relationship(
        "FeedMapper", back_populates="feed", uselist=False, cascade="all,delete-orphan"
    )
