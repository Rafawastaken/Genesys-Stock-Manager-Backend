# app/models/feed_mapper.py
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infra.base import Base, utcnow


class FeedMapper(Base):
    __tablename__ = "feed_mappers"
    __table_args__ = (UniqueConstraint("id_feed", name="uq_feed_mappers_id_feed"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_feed: Mapped[int] = mapped_column(
        ForeignKey("supplier_feeds.id", ondelete="CASCADE"), index=True
    )

    profile_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime, onupdate=utcnow, default=utcnow, nullable=True
    )

    feed = relationship("SupplierFeed", back_populates="mapper")
