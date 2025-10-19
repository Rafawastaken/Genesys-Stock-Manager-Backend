# app/models/feed_run.py
# This module defines the FeedRun model representing the execution of a supplier feed.

from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, ForeignKey, DateTime, Text
from app.infra.base import Base, utcnow
from app.models.enums import RUN_STATUS

class FeedRun(Base):
    __tablename__ = "feed_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    feed_id: Mapped[int] = mapped_column(Integer, ForeignKey("supplier_feeds.id", ondelete="CASCADE"), index=True)
    started_at:  Mapped[DateTime] = mapped_column(DateTime, default=utcnow)
    finished_at: Mapped[Optional[DateTime]] = mapped_column(DateTime, default=None)
    status: Mapped[str] = mapped_column(RUN_STATUS, default="running", nullable=False)
    http_status:  Mapped[Optional[int]] = mapped_column(Integer, default=None)
    rows_total:   Mapped[int] = mapped_column(Integer, default=0)
    rows_changed: Mapped[int] = mapped_column(Integer, default=0)
    duration_ms:  Mapped[Optional[int]] = mapped_column(Integer, default=None)
    error_msg:    Mapped[Optional[str]] = mapped_column(Text, default=None)

    feed: Mapped["SupplierFeed"] = relationship("SupplierFeed", back_populates="runs")
